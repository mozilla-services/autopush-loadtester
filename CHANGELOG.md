<a name="0.1"></a>
## 0.1 (2015-12-30)


#### Chore

*   add clog config for writing changelogs ([fe44c40b](https://github.com/mozilla-services/ap-loadtester/commit/fe44c40b61aceb9c7172813ee9b01f679b9b50b1))
*   0.1 release ([e910351d](https://github.com/mozilla-services/ap-loadtester/commit/e910351d26a5e7058ff6de01dd79a028db5716b6))
*   switch fake key used ([6e47d79b](https://github.com/mozilla-services/ap-loadtester/commit/6e47d79b3792e4c1698a554cbbcd25a8e404c076))
*   pin txaio as latest version needs extra options ([5377f7b2](https://github.com/mozilla-services/ap-loadtester/commit/5377f7b2fbfdd3c8af7cba0110be1029867293e3))
*   add missin setup.cfg to ensure coverage options are run properly ([ad7e2b7d](https://github.com/mozilla-services/ap-loadtester/commit/ad7e2b7d970f468d93d7681ae905f896ac4af4d1))
*   ensure codecov is available to travis ([d50b0114](https://github.com/mozilla-services/ap-loadtester/commit/d50b0114cbc12514cc3d034820b236986bef296c))
*   add codecov and build images to readme ([7a074c49](https://github.com/mozilla-services/ap-loadtester/commit/7a074c494f64398da6aa3dd3d37c9871d4877e24))
*   ignore the coverage reports ([4d96ac5d](https://github.com/mozilla-services/ap-loadtester/commit/4d96ac5df9719bffa82558fa613148f6397b9828))
*   update gitignore for .tox dir ([a078573d](https://github.com/mozilla-services/ap-loadtester/commit/a078573dfe0ed400d8a0dbb11624b15d81c13bb0))
*   setup tox/travis for automated testing ([5b9d04ff](https://github.com/mozilla-services/ap-loadtester/commit/5b9d04ffabc327ec7b5807e9b544d17b55edb0f9))
*   remove unneeded requirements.txt as this is more of a library/program than application ([0193e7a3](https://github.com/mozilla-services/ap-loadtester/commit/0193e7a371465f6b31ead947be3a4a50779861f8))
*   add egg-info to gitignore ([770ee5e9](https://github.com/mozilla-services/ap-loadtester/commit/770ee5e9fc8a74e0312349d465ee944f42876e69))
*   add basic setup.py for a python project ([b5fa635e](https://github.com/mozilla-services/ap-loadtester/commit/b5fa635e84f3d5d28d5b4b59ad870a8801ca2be6))
*   add basic project requirements ([c09ce7a8](https://github.com/mozilla-services/ap-loadtester/commit/c09ce7a8812c6c1680409698b7a1dabe599c4442))
*   add CONTRIBUTING guideline ([97d24db4](https://github.com/mozilla-services/ap-loadtester/commit/97d24db4303fdb2b3979602aa4e8426644d3c393))
*   add gitignore for basic python files ([735fba3d](https://github.com/mozilla-services/ap-loadtester/commit/735fba3d4773017942c52307f4de7b1993da34df))
*   Add empty readme to initial repo ([f1ef1f07](https://github.com/mozilla-services/ap-loadtester/commit/f1ef1f07273d936280dcdf0ad282e6ffa1f7138a))
*   setup initial repo skeleton ([c9daef55](https://github.com/mozilla-services/ap-loadtester/commit/c9daef55cf4b31131a6632a00bd57b4215020bb2))

#### Features

*   add connect and idle forever scenario for connection load-testing ([64ebdc15](https://github.com/mozilla-services/ap-loadtester/commit/64ebdc154ee07542da1228b7502a9f80ba77d691))
*   add verification of testplan args, and scenario function arguments ([d84c5bf3](https://github.com/mozilla-services/ap-loadtester/commit/d84c5bf3c8f351a62b6607b5c4ff2a52e1da8272))
*   port reconnect and basic notification scenarios from haskell version and tests to verify them ([30c47a3d](https://github.com/mozilla-services/ap-loadtester/commit/30c47a3dad489ce077bb706d821f4abd85826d6a))
*   add random_data command to generate binary data of various lengths randomly ([1cd8a8ad](https://github.com/mozilla-services/ap-loadtester/commit/1cd8a8ad72fb71d09a27cf99ffc7312a5e471018))
*   add metric commands for timer start/end and counter ([1c78ccdc](https://github.com/mozilla-services/ap-loadtester/commit/1c78ccdc02be23fb9e46876f95a2c2114e764fc9))
*   add dockerfile for trusted docker builds ([2d70699f](https://github.com/mozilla-services/ap-loadtester/commit/2d70699f1778b604ec2fbe1d1692e806db17597b))
*   add ability for aplt_scenario to pass arguments to scenarios ([4303e94b](https://github.com/mozilla-services/ap-loadtester/commit/4303e94b3d59f11c229740c0437c1bad56440954))
*   add aplt_testplan script that runs a full testplan refactor: separate CLI bits into modular parsing functions test: add test for aplt_testplan script feat: add ability to use scenario arguments with aplt_testplan ([8cb12383](https://github.com/mozilla-services/ap-loadtester/commit/8cb12383ce4f938ba10009514295888f459444a0))
*   add ability to specify the websocket server to run against ([386ee0ed](https://github.com/mozilla-services/ap-loadtester/commit/386ee0edbc682c26f017fddfedf0d75fd8ab0132))
*   add complete working client with scenario runner script and updated requirements/setup for runner script ([5a17ee94](https://github.com/mozilla-services/ap-loadtester/commit/5a17ee94f6a6844f5a9f1d34283607f2f64b0cee))
*   add a basic client interaction scenario ([e41a8ba4](https://github.com/mozilla-services/ap-loadtester/commit/e41a8ba488df368eb0f7f7e35b83d8a53cd80176))
*   add initial client command processor, commands, and websocket client ([f34917d1](https://github.com/mozilla-services/ap-loadtester/commit/f34917d1470e2064f09ab2b00d8c52b36b599b93))

#### Bug Fixes

*   remove debug line in verify_arguments ([d13fb397](https://github.com/mozilla-services/ap-loadtester/commit/d13fb397a52916663a91042d20e67350849dfc60))
*   switch default namespace to match existing load tester ([4bee2208](https://github.com/mozilla-services/ap-loadtester/commit/4bee2208917ba6a7c73323ded4e7b08447b7b427))
*   ensure empty args are handled as such for a scenario ([887fcc86](https://github.com/mozilla-services/ap-loadtester/commit/887fcc866ab008067a951e761275ea1034feb9f2))
*   parse scenario args for aplt_scenario command properly ([472f7629](https://github.com/mozilla-services/ap-loadtester/commit/472f762955e2a8cf18d13561bbf782b011c24ae5))
*   switch order of connect to ensure the processor is ready when the connection comes up ([69c73394](https://github.com/mozilla-services/ap-loadtester/commit/69c733943a97a13e8d28e63bdb4e9f1291940af1))
*   add requirements since txstatsd is not pip installable and change README to reflect using easy_install for lib use ([e67529ff](https://github.com/mozilla-services/ap-loadtester/commit/e67529ff67217ccbf37521379f35ecd84a20ce3a))
*   indicate for txaio that twisted is being used ([d5058964](https://github.com/mozilla-services/ap-loadtester/commit/d50589646589caf1530209064c8342d09d15db5b))
*   update basic integration so it passes ([f461dfd6](https://github.com/mozilla-services/ap-loadtester/commit/f461dfd6f28e582b05ad687d937e4911e3e1c39d))

#### Refactor

*   add parse_string_to_list and utilize it where appropriate to parse the string args ([74681156](https://github.com/mozilla-services/ap-loadtester/commit/7468115637630443f37d912a6a9b5b3ee52bba1e))
*   switch harness to only be responsible for a single scenario, place skeleton for load runner into place ([ccf7ac4b](https://github.com/mozilla-services/ap-loadtester/commit/ccf7ac4b2603031977cecdde9f07d530389cb1df))
*   move reactor control out of the harness ([89724199](https://github.com/mozilla-services/ap-loadtester/commit/89724199f6b3b8d67e579b87ba71386f093e990c))
*   use abstract requirements in setup file ([5f8fb9d5](https://github.com/mozilla-services/ap-loadtester/commit/5f8fb9d5169743d5067f86e0e44fbb53ed4cccac))

#### Doc

*   add scenario docs and link from readme ([d4573a75](https://github.com/mozilla-services/ap-loadtester/commit/d4573a7574cfffedc33f1d9a09648bbc571c7536), closes [#4](https://github.com/mozilla-services/ap-loadtester/issues/4))
*   add Installation notes to README ([65c16545](https://github.com/mozilla-services/ap-loadtester/commit/65c165455f956dc9e4f49563222368fee65698f8))
*   fix developing section of README ([9eb7c5de](https://github.com/mozilla-services/ap-loadtester/commit/9eb7c5deff611ba72e2bcb8837eb7019204cf30e))
*   remove node specific bits from contributing ([37659bb2](https://github.com/mozilla-services/ap-loadtester/commit/37659bb2637159b3203e733338a816468732664c))
*   add information about installing as a library, and running a single scenario ([fb98d08b](https://github.com/mozilla-services/ap-loadtester/commit/fb98d08b0aeb8eb16f6e50519942186da0df33e6))
*   add developing doc on how to develop the codebase ([3982eecd](https://github.com/mozilla-services/ap-loadtester/commit/3982eecde4ad5061eaad474e3fd4b50c15728166))

#### Test

*   fix test fail due to missing scenario args ([aaaf96f3](https://github.com/mozilla-services/ap-loadtester/commit/aaaf96f3aa64e9ae2972b060d57292582192fe90))
*   add more thorough harness tests, and bad scenario integration test ([baad6e71](https://github.com/mozilla-services/ap-loadtester/commit/baad6e7150317cf74b21f689671045a9b32116de))
*   add codecov for test run ([14309bca](https://github.com/mozilla-services/ap-loadtester/commit/14309bca0e78afdba2d5f768efb185955cb95140))
*   add initial non-working integration test ([da10b918](https://github.com/mozilla-services/ap-loadtester/commit/da10b9184717bb90102491528c865e0d4ba22ebd))



