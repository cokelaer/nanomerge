#
#  This file is part of Sequana software
#
#  Copyright (c) 2016-2021 - Sequana Dev Team (https://sequana.readthedocs.io)
#
#  Distributed under the terms of the 3-clause BSD license.
#  The full license is in the LICENSE file, distributed with this software.
#
#  Website:       https://github.com/sequana/sequana
#  Documentation: http://sequana.readthedocs.io
#  Contributors:  https://github.com/sequana/sequana/graphs/contributors
##############################################################################
import sys
import os
import argparse
import shutil
import subprocess
from pathlib import Path

from sequana_pipetools.options import *
from sequana_pipetools.misc import Colors
from sequana_pipetools.info import sequana_epilog, sequana_prolog
from sequana_pipetools import SequanaManager

col = Colors()

NAME = "nanomerge"


class Options(argparse.ArgumentParser):
    def __init__(self, prog=NAME, epilog=None):
        usage = col.purple(sequana_prolog.format(**{"name": NAME}))
        super(Options, self).__init__(
            usage=usage,
            prog=prog,
            description="",
            epilog=epilog,
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        )

        # add a new group of options to the parser
        so = SlurmOptions()
        so.add_options(self)

        # add a snakemake group of options to the parser
        so = SnakemakeOptions(working_directory=NAME)
        so.add_options(self)

        so = InputOptions(add_input_readtag=False)
        so.add_options(self)

        so = GeneralOptions()
        so.add_options(self)

        pipeline_group = self.add_argument_group("pipeline")

        pipeline_group.add_argument("--samplesheet", help="a CSV with 3 columns named project,sample,barcode ",
default=None, type=str, dest="samplesheet", required=True)
        pipeline_group.add_argument("--summary", help="a summary file generated by albacore or guppy. if provided,pyqoQC is used to generate a HTML report. ", default=None, type=str, dest="summary")


        self.add_argument("--run", default=False, action="store_true",
            help="execute the pipeline directly")
    def parse_args(self, *args):
        args_list = list(*args)
        if "--from-project" in args_list:
            if len(args_list) > 2:
                msg = (
                    "WARNING [sequana]: With --from-project option, "
                    + "pipeline and data-related options will be ignored."
                )
                print(col.error(msg))
            for action in self._actions:
                if action.required is True:
                    action.required = False
        options = super(Options, self).parse_args(*args)
        return options


def main(args=None):

    if args is None:
        args = sys.argv

    # whatever needs to be called by all pipeline before the options parsing
    from sequana_pipetools.options import before_pipeline

    before_pipeline(NAME)

    # option parsing including common epilog
    options = Options(NAME, epilog=sequana_epilog).parse_args(args[1:])

    # the real stuff is here
    manager = SequanaManager(options, NAME)

    # create the beginning of the command and the working directory
    manager.setup()


    # fill the config file with input parameters
    if options.from_project is None:
        # fill the config file with input parameters
        cfg = manager.config.config
        # EXAMPLE TOREPLACE WITH YOUR NEEDS
        cfg.input_directory = os.path.abspath(options.input_directory)
        cfg.input_pattern = options.input_pattern
        if os.path.exists(options.samplesheet):
            shutil.copy(options.samplesheet, manager.workdir)
            cfg.samplesheet = Path(options.samplesheet).name
        else:
            raise IOError(f"{options.samplesheet} not found. Requested to perfom the merge of FastQ files")

        if options.summary:
            if os.path.exists(options.summary):
                shutil.copy(options.summary, manager.workdir)
                cfg.summary = Path(options.summary).name
            elif not os.path.exists(options.summary):
                raise IOError(f"{options.summary} not found. Check your input filename")
        else:
            cfg.summary = None


    # finalise the command and save it; copy the snakemake. update the config
    # file and save it.
    manager.teardown()

    if options.run:
        subprocess.Popen(["sh", '{}.sh'.format(NAME)], cwd=options.workdir)


if __name__ == "__main__":
    main()
