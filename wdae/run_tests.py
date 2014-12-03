import sys
import argparse
import unittest

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
    from functional_tests.tests.functional_helpers import test_results_mode, \
         save_variants_results, test_results_mode_enrichment, save_results_mode_enrichment

    args = parse_cli_arguments(sys.argv[1:])
    context = dict(args._get_kwargs())
    if args.mode == 'save':
        if not args.enrichment_requests is None:
             save_results_mode_enrichment(args.url,
                                          args.enrichment_requests,
                                          args.results_dir)
        if not args.variants_requests is None:
            save_variants_results(**context)
            
    elif args.mode == 'test':
        if not args.enrichment_requests is None:
            test_results_mode_enrichment(args.url,
                                         args.enrichment_requests,
                                         args.results_dir)
        if not args.variants_requests is None:
            from functional_tests.tests.functional_runner import build_variants_test_suite, \
                cleanup_variants_test, test_report, SeqpipeTestResult
            
            variants_context, suite = build_variants_test_suite(**context)
    
            runner = unittest.TextTestRunner(resultclass = SeqpipeTestResult)
            result = runner.run(suite)

            cleanup_variants_test(**variants_context)
            
            test_report(result)            
    else:
        print("unexpected mode (%s)" % args.mode)
        
    