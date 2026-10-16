"""확장자 오인, 본문 누락과 손상된 문서의 성공 오인을 방지한다."""
import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import struct
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from zipfile import ZipFile
import zlib

from savetax.cli import main


def archive(path, entries):
    with ZipFile(path, 'w') as z:
        for name, value in entries.items():
            z.writestr(name, value)
    return path


def section(text):
    return f'<sec xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph"><hp:p><hp:run><hp:t>{text}</hp:t></hp:run></hp:p></sec>'


class DocumentTests(unittest.TestCase):
    def test_cli_detects_hwpx_bytes_and_preserves_origin_without_validating_specs(self):
        with tempfile.TemporaryDirectory() as folder:
            src=archive(Path(folder)/'wrong.hwp',{'Contents/section0.xml':section('모델 MD-25S, 두께 25mm')})
            dst=Path(folder)/'out.json'
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(main(['document-read','--input',str(src),'--output',str(dst)]),0)
            result=json.loads(dst.read_text(encoding='utf-8'))
            self.assertEqual(result['format'],'hwpx')
            self.assertTrue(result['extension_mismatch'])
            self.assertIn('MD-25S',result['text'])
            self.assertEqual(result['sha256'],hashlib.sha256(src.read_bytes()).hexdigest())
            self.assertEqual(result['evidence_status'],'unreviewed_text_extraction')

    def test_hwpx_follows_spine_and_keeps_nested_table_text_once(self):
        from savetax.documents import read_document
        hpf='<package><manifest><item id="a" href="section10.xml"/><item id="b" href="section2.xml"/></manifest><spine><itemref idref="b"/><itemref idref="a"/></spine></package>'
        nested='<sec><p><run><t>앞</t><tbl><p><run><t>셀</t></run></p></tbl><t>뒤</t></run></p></sec>'
        with tempfile.TemporaryDirectory() as folder:
            src=archive(Path(folder)/'x.hwpx',{'Contents/content.hpf':hpf,'Contents/section10.xml':nested,'Contents/section2.xml':section('첫 구역')})
            result=read_document(src)
        self.assertEqual([s['name'] for s in result['sections']],['Contents/section2.xml','Contents/section10.xml'])
        self.assertEqual(result['text'],'첫 구역\n앞\n셀\n뒤')
        self.assertEqual(result['text'].count('셀'),1)

    def test_hwpx_numeric_order_fallback_is_explicit(self):
        from savetax.documents import read_document
        with tempfile.TemporaryDirectory() as folder:
            src=archive(Path(folder)/'x.hwpx',{'Contents/section10.xml':section('열'),'Contents/section2.xml':section('둘')})
            result=read_document(src)
        self.assertEqual(result['text'],'둘\n열')
        self.assertEqual(result['section_order'],'numeric_filename_fallback')

    def test_hwpx_malformed_or_unsafe_input_does_not_produce_evidence(self):
        from savetax.documents import read_document
        for entries in [
            {'../Contents/section0.xml':section('x')},
            {'Contents/section0.xml':'<!DOCTYPE a [<!ENTITY x "injected">]><p><t>&x;</t></p>'},
            {'Contents/section0.xml':'<?xml version="1.0" encoding="utf-16"?><!DOCTYPE a [<!ENTITY x "injected">]><p><t>&x;</t></p>'.encode('utf-16')},
            {'Contents/section0.xml':'<unclosed>'},
            {'Contents/section0.xml':section('ok'),'Contents/content.hpf':'<package><spine><itemref idref="missing"/></spine></package>'},
        ]:
            with self.subTest(entries=list(entries)),tempfile.TemporaryDirectory() as folder:
                src=archive(Path(folder)/'x.hwpx',entries)
                with self.assertRaises(ValueError):read_document(src)

    def test_document_size_limits_are_enforced_before_text_success(self):
        from savetax.documents import read_document
        with tempfile.TemporaryDirectory() as folder:
            src=archive(Path(folder)/'x.hwpx',{'Contents/section0.xml':section('내용'*100)})
            with self.assertRaises(ValueError):read_document(src,max_file_bytes=20)
            with self.assertRaises(ValueError):read_document(src,max_expanded_bytes=30)

    def test_hwp_compressed_and_plain_records_skip_inline_control_payload(self):
        from savetax.documents import read_document
        # A table-control's twelve payload bytes look like text; they must not leak.
        payload='앞'.encode('utf-16le')+struct.pack('<H',11)+b'X'*12+struct.pack('<H',11)+'뒤\r'.encode('utf-16le')
        record=struct.pack('<I',67 | (len(payload)<<20))+payload
        for compressed in (False,True):
            header=b'HWP Document File'.ljust(32,b'\0')+struct.pack('<II',0x05000300,int(compressed))+b'\0'*216
            stream=record
            if compressed:
                c=zlib.compressobj(wbits=-15);stream=c.compress(record)+c.flush()
            streams={'FileHeader':header,'BodyText/Section0':stream}
            fake=SimpleNamespace(openstream=lambda key:io.BytesIO(streams[key]),listdir=lambda:[['BodyText','Section0']],close=lambda:None)
            with self.subTest(compressed=compressed),tempfile.TemporaryDirectory() as folder:
                src=Path(folder)/'misnamed.hwpx';src.write_bytes(bytes.fromhex('d0cf11e0a1b11ae1'))
                with patch.dict('sys.modules',{'olefile':SimpleNamespace(OleFileIO=lambda _:fake)}):
                    result=read_document(src)
                self.assertEqual(result['format'],'hwp')
                self.assertEqual(result['text'],'앞뒤')
                self.assertTrue(result['extension_mismatch'])

    def test_protected_hwp_is_not_returned_as_readable(self):
        from savetax.documents import read_document
        header=b'HWP Document File'.ljust(32,b'\0')+struct.pack('<II',0x05000300,2)+b'\0'*216
        fake=SimpleNamespace(openstream=lambda _:io.BytesIO(header),close=lambda:None)
        with tempfile.TemporaryDirectory() as folder:
            src=Path(folder)/'x.hwp';src.write_bytes(bytes.fromhex('d0cf11e0a1b11ae1'))
            with patch.dict('sys.modules',{'olefile':SimpleNamespace(OleFileIO=lambda _:fake)}):
                with self.assertRaises(ValueError):read_document(src)

    def test_truncated_hwp_record_does_not_invent_partial_text(self):
        from savetax.documents import read_document
        header=b'HWP Document File'.ljust(32,b'\0')+struct.pack('<II',0x05000300,0)+b'\0'*216
        streams={'FileHeader':header,'BodyText/Section0':struct.pack('<I',67|(100<<20))+b'xx'}
        fake=SimpleNamespace(openstream=lambda key:io.BytesIO(streams[key]),listdir=lambda:[['BodyText','Section0']],close=lambda:None)
        with tempfile.TemporaryDirectory() as folder:
            src=Path(folder)/'x.hwp';src.write_bytes(bytes.fromhex('d0cf11e0a1b11ae1'))
            with patch.dict('sys.modules',{'olefile':SimpleNamespace(OleFileIO=lambda _:fake)}):
                with self.assertRaises(ValueError):read_document(src)

    def test_hwp_valid_crc_size_trailer_is_accepted_but_bad_crc_is_not(self):
        from savetax.documents import read_document
        payload='정상 본문'.encode('utf-16le')
        record=struct.pack('<I',67|(len(payload)<<20))+payload
        c=zlib.compressobj(wbits=-15);compressed=c.compress(record)+c.flush()
        header=b'HWP Document File'.ljust(32,b'\0')+struct.pack('<II',0x05000300,1)+b'\0'*216
        for crc,accepted in [(zlib.crc32(record),True),(zlib.crc32(record)^1,False)]:
            streams={'FileHeader':header,'BodyText/Section0':compressed+struct.pack('<II',crc,len(record))}
            fake=SimpleNamespace(openstream=lambda key:io.BytesIO(streams[key]),listdir=lambda:[['BodyText','Section0']],close=lambda:None)
            with self.subTest(valid=accepted),tempfile.TemporaryDirectory() as folder:
                src=Path(folder)/'x.hwp';src.write_bytes(bytes.fromhex('d0cf11e0a1b11ae1'))
                with patch.dict('sys.modules',{'olefile':SimpleNamespace(OleFileIO=lambda _:fake)}):
                    if accepted:self.assertEqual(read_document(src)['text'],'정상 본문')
                    else:
                        with self.assertRaises(ValueError):read_document(src)

    def test_cli_refuses_to_overwrite_the_source_document(self):
        with tempfile.TemporaryDirectory() as folder:
            src=archive(Path(folder)/'x.hwpx',{'Contents/section0.xml':section('원본')})
            before=src.read_bytes()
            with contextlib.redirect_stderr(io.StringIO()),contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(main(['document-read','--input',str(src),'--output',str(src)]),2)
            self.assertEqual(src.read_bytes(),before)

    def test_negative_read_limit_does_not_become_an_unbounded_read(self):
        from savetax.documents import read_document
        with tempfile.TemporaryDirectory() as folder:
            src=Path(folder)/'missing.hwpx'
            with self.assertRaises(ValueError):read_document(src,max_file_bytes=-2)

    def test_cli_rejects_existing_temp_hardlink_to_source(self):
        with tempfile.TemporaryDirectory() as folder:
            src=archive(Path(folder)/'source.hwpx',{'Contents/section0.xml':section('원본')})
            dst=Path(folder)/'result.json'
            os.link(src,dst.with_suffix('.json.tmp'))
            before=src.read_bytes()
            with contextlib.redirect_stderr(io.StringIO()),contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(main(['document-read','--input',str(src),'--output',str(dst)]),2)
            self.assertEqual(src.read_bytes(),before)


if __name__=='__main__':unittest.main()
