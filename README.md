# pyQMR - python MapReduce implementation using qsub

python module that implements the MapReduce parallelization paradigm by
transparently constructing, submitting, and monitoring qsub jobs. MapReduce
jobs are specified entirely in python function calls, no extra configuration
scripts necessary, short of specifying any environment-specific qsub options
(e.g. -P, etc).

