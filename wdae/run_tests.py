import sys
import argparse
import unittest

from functional_tests.tests.functional_runner import build_test_suite, \
    cleanup_variants_test, test_report, save_test_suite, SeqpipeTestResult
# from functional_tests.tests.functional_helpers import test_results_mode, \
#          save_variants_results, test_results_mode_enrichment, save_results_mode_enrichment

def parse_cli_arguments(argv=sys.argv[1:]):
    parser = argparse.ArgumentParser(description="Functional tests runner.")
    parser.add_argument('--url', type=str,
                        default=None,
                        help='''server url to test: e.g. "http://seqpipe-vm.setelis.com/dae"''')

    parser.add_argument('--variants-requests', type=str, default=None,
                        help='''file containing list of request dictionaries''')
    
    parser.add_argument('--enrichment-requests', type=str, default=None,
                        help='''file containing list of request dictionaries''')

    parser.add_argument('--results-dir', type=str, default=None,
                    help='''directory where results are/should be stored''')

    parser.add_argument('--data-dir', type=str, default=None,
                    help='''directory where patterns are stored''')

    parser.add_argument('--mode', type=str, default='test',
                        help='the mode to run: "test" and "save" mode')
    args = parser.parse_args(argv)
    if args.url is None:
        print('--url argurment is required')
        parser.print_help()
        sys.exit(1)
    if args.variants_requests is None and args.enrichment_requests is None:
        print('requests data (variants or enrichment) argument is required')
        parser.print_help()
        sys.exit(1)  
    if args.results_dir is None:
        print('--results-dir argument is required')
        parser.print_help()
        sys.exit(1)
    if args.mode != 'test' and args.mode != 'save':
        print('unexpected mode (%s)' % args.mode)
        parser.print_help()
        sys.exit(1)
        
    return args


if __name__ == "__main__":

    args = parse_cli_arguments(sys.argv[1:])
    context = dict(args._get_kwargs())

    test_context, suite = build_test_suite(**context)
    
    if args.mode == 'save':
        save_test_suite(suite)
        cleanup_variants_test(**test_context)
        return 0
        
    elif args.mode == 'test':
        runner = unittest.TextTestRunner(resultclass = SeqpipeTestResult)
        result = runner.run(suite)
        test_report(result)            
        cleanup_variants_test(**test_context)
        if result.failures or result.errors:
            return 1
        else:
            return 0
    else:
        print("unexpected mode (%s)" % args.mode)
        return 1
    