<a name="0.1"></a>
## 0.1 (2015-12-30)


#### Features

*   add connect and idle forever scenario for connection load-testing ([64ebdc15](64ebdc15))
*   add verification of testplan args, and scenario function arguments ([d84c5bf3](d84c5bf3))
*   port reconnect and basic notification scenarios from haskell version and tests to verify them ([30c47a3d](30c47a3d))
*   add random_data command to generate binary data of various lengths randomly ([1cd8a8ad](1cd8a8ad))
*   add metric commands for timer start/end and counter ([1c78ccdc](1c78ccdc))
*   add dockerfile for trusted docker builds ([2d70699f](2d70699f))
*   add ability for aplt_scenario to pass arguments to scenarios ([4303e94b](4303e94b))
*   add aplt_testplan script that runs a full testplan ([8cb12383](8cb12383))
*   add ability to use scenario arguments with aplt_testplan ([8cb12383](8cb12383))
*   add ability to specify the websocket server to run against ([386ee0ed](386ee0ed))
*   add complete working client with scenario runner script and updated requirements/setup for runner script ([5a17ee94](5a17ee94))
*   add a basic client interaction scenario ([e41a8ba4](e41a8ba4))
*   add initial client command processor, commands, and websocket client ([f34917d1](f34917d1))

#### Doc

*   add scenario docs and link from readme ([d4573a75](d4573a75), closes [#4](4))
*   add Installation notes to README ([65c16545](65c16545))
*   fix developing section of README ([9eb7c5de](9eb7c5de))
*   remove node specific bits from contributing ([37659bb2](37659bb2))
*   add information about installing as a library, and running a single scenario ([fb98d08b](fb98d08b))
*   add developing doc on how to develop the codebase ([3982eecd](3982eecd))

#### Chore

*   switch fake key used ([6e47d79b](6e47d79b))
*   pin txaio as latest version needs extra options ([5377f7b2](5377f7b2))
*   add missin setup.cfg to ensure coverage options are run properly ([ad7e2b7d](ad7e2b7d))
*   ensure codecov is available to travis ([d50b0114](d50b0114))
*   add codecov and build images to readme ([7a074c49](7a074c49))
*   ignore the coverage reports ([4d96ac5d](4d96ac5d))
*   update gitignore for .tox dir ([a078573d](a078573d))
*   setup tox/travis for automated testing ([5b9d04ff](5b9d04ff))
*   remove unneeded requirements.txt as this is more of a library/program than application ([0193e7a3](0193e7a3))
*   add egg-info to gitignore ([770ee5e9](770ee5e9))
*   add basic setup.py for a python project ([b5fa635e](b5fa635e))
*   add basic project requirements ([c09ce7a8](c09ce7a8))
*   add CONTRIBUTING guideline ([97d24db4](97d24db4))
*   add gitignore for basic python files ([735fba3d](735fba3d))
*   Add empty readme to initial repo ([f1ef1f07](f1ef1f07))
*   setup initial repo skeleton ([c9daef55](c9daef55))

#### Bug Fixes

*   remove debug line in verify_arguments ([d13fb397](d13fb397))
*   switch default namespace to match existing load tester ([4bee2208](4bee2208))
*   ensure empty args are handled as such for a scenario ([887fcc86](887fcc86))
*   parse scenario args for aplt_scenario command properly ([472f7629](472f7629))
*   switch order of connect to ensure the processor is ready when the connection comes up ([69c73394](69c73394))
*   add requirements since txstatsd is not pip installable and change README to reflect using easy_install for lib use ([e67529ff](e67529ff))
*   indicate for txaio that twisted is being used ([d5058964](d5058964))
*   update basic integration so it passes ([f461dfd6](f461dfd6))

#### Test

*   add test for aplt_testplan script ([8cb12383](8cb12383))
*   fix test fail due to missing scenario args ([aaaf96f3](aaaf96f3))
*   add more thorough harness tests, and bad scenario integration test ([baad6e71](baad6e71))
*   add codecov for test run ([14309bca](14309bca))
*   add initial non-working integration test ([da10b918](da10b918))

#### Refactor

*   separate CLI bits into modular parsing functions ([8cb12383](8cb12383))
*   add parse_string_to_list and utilize it where appropriate to parse the string args ([74681156](74681156))
*   switch harness to only be responsible for a single scenario, place skeleton for load runner into place ([ccf7ac4b](ccf7ac4b))
*   move reactor control out of the harness ([89724199](89724199))
*   use abstract requirements in setup file ([5f8fb9d5](5f8fb9d5))
