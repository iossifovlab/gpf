import sys
import argparse

def parse_cli_arguments(argv=sys.argv[1:]):
    parser = argparse.ArgumentParser(description="Functional tests runner.")
    parser.add_argument('--url', type=str,
                        default=None,
                        help='''server url to test: e.g. "http://seqpipe-vm.setelis.com/dae"''')

    parser.add_argument('--variants-requests', type=str, default=None,
                        help='''file containing list of request dictionaries''')

    parser.add_argument('--results-dir', type=str, default=None,
                    help='''dictionary where results are/should be stored''')

    parser.add_argument('--mode', type=str, default='test',
                        help='the mode to run: "test" and "save" mode')
    args = parser.parse_args(argv)
    if args.url is None:
        print('--url argurment is required')
        parser.print_help()
        sys.exit(1)
    if args.variants_requests is None:
        print('--requests-data argument is required')
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
    from functional_tests.tests.functional_tests_helpers import test_results_mode, \
        save_results_mode

    args = parse_cli_arguments(sys.argv[1:])
    if args.mode == 'save':
        save_results_mode(args.url,
                          args.variants_requests,
                          args.results_dir)
    elif args.mode == 'test':
        test_results_mode(args.url,
                          args.variants_requests,
                          args.results_dir)
    else:
        print("unexpected mode (%s)" % args.mode)
        
    