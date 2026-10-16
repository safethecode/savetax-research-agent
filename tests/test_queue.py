import unittest

from savetax.queue import prioritize


class QueueTests(unittest.TestCase):
    def test_large_verified_new_items_first_and_small_savings_deferred(self):
        rows = [{'item_id':'small','state':'available','verified':True,'eligible_for_preview':True,'potential_savings_krw':'50000000'},
                {'item_id':'large','state':'available','verified':True,'eligible_for_preview':True,'potential_savings_krw':'300000000'},
                {'item_id':'duplicate','state':'claimed','verified':True,'eligible_for_preview':True,'potential_savings_krw':'9000000000'},
                {'item_id':'unknown','state':'available','verified':False,'eligible_for_preview':False,'potential_savings_krw':None}]
        out = prioritize(rows,remaining=5)
        self.assertEqual([r['item_id'] for r in out['submit_now']],['large'])
        self.assertEqual([r['item_id'] for r in out['deferred']],['small'])
        self.assertEqual([r['item_id'] for r in out['excluded_duplicates']],['duplicate'])

    def test_deferred_only_released_when_requested_and_quota_remains(self):
        rows = [{'item_id':'s','state':'available','verified':True,'eligible_for_preview':True,'potential_savings_krw':'50000000'}]
        self.assertFalse(prioritize(rows,remaining=0,release_deferred=True)['submit_now'])
        self.assertEqual(len(prioritize(rows,remaining=1,release_deferred=True)['submit_now']),1)


if __name__ == '__main__':
    unittest.main()
