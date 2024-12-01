# Transformo

Transformo is a generalized software package for estimating geodetic transformation
parameters and models.

Transformo seeks to provide a framework that lets the user focus on determining the
best transformation model. To achieve that, the burden of reading coordinate data
from various sources, (re)implementing algorimths and delivering the results in
a useful an accessable form has been removed.

The main problem Transformo tries to solve can be presented on the idealized form

```
T = M(p, S)
```

Where `S` and `T` are the source and target coordinates, `M` is a transformation
model and `p` is the parameters for the chosen model.

The real world is rarely simple so a more realistic form would be

```
T = M(p, S) + R
```

Where `R` is the transformation residuals.

The primary function of Transformo is to provide a set of parameters `p` that
minimizesthe residual `R`. In some cases that might involve a transformation model
consisting of several steps:

```
T = M3(p3, M2(p2, M1(p1, S))) + R
```

With transformo we can easily specify the `S`, `T` and `M1`, `M2`, and `M3` using
the built-in constructs, which leaves only the parameters, `p1`, `p2` and `p3`, to
be determined. Transformo will do that based on the specified model and present
the results in a suitable format.

## Rationale

The rationale behind Transformo is to create a framework that removes the tedious
work of reading input data and presenting the results after transformation
parameters has been determined. In particular, this approch is meant to be a service
to researchers that develop new for methods geodetic coordinate transformations, as
they can focus on the core algorithms and not the supporting scaffolding.

## Installation

Transformo is best run in a Conda environment. Clone the repository from GitHub
and run the following commands in the root:

```sh
mamba env create -f environment.yml
mamba activate transformo
pip install .
```

## Using Transformo

Transformo is a command line application that expects a YAML-file as input.
The YAML-file defines a pipeline of datasources, operators and presenters.
Once the pipeline has been processed by Transformo the results can be displayed
in the terminal or saved to a file in various formats.

Here's an example:

```sh
transformo pipeline.yaml --pdf pipeline.yaml
```

which will produce a PDF-file with the results of the processed pipeline.

The file `pipeline.yaml` might look something like:

```yaml
source_data:
- name: ITRF2014
  type: csv
  filename: test/data/dk_cors_itrf2014.csv
target_data:
- name: ETRS89
  type: csv
  filename: test/data/dk_cors_etrs89.csv
operators:
- type: helmert_translation
presenters:
- name: PROJ string
  type: proj_presenter
- name: Coordinates
  type: coordinate_presenter
```

Note that some pipeline entries are named and some aren't. The name attribute
is optional but are useful when working with bigger pipelines. For named
presenters the name will used as section headers for the presenter output in the
report.

## Use cases

* Estimate a 7-parameter Helmert transformation
* Derive the next iteration of the NKG Transformations
* Adjust a geoid model to a height system
* ...

## Architecture

The overall architecture consists of a pipeline on the form

```
DATASOURCE_1                                                        PRESENTER_1

DATASOURCE_2                                                        PRESENTER_2

DATASOURCE_3   -> OPERATOR_1 -> OPERATOR_2 -> ... > OPERATOR_N ->   PRESENTER_3

    ...                                                              ...

DATASOURCE_N                                                        PRESENTER_N
```

where *datasources* gathers sets of source and target coordinates and velocities and
assembles them in a standardized internal form and *writers* presents the derived
transformation model in standardized formats.

The *operators* derive parameters for selected transformation techniques, for
instance a Helmert transformation. In case of several chained operators the later
steps are presented with the residuals of the earlier transformation estimate for
which the current operator can attemt to reduce even further using a different
transformations technique.

### Datasources

Datasources consumes data from a single data source and provide it on a standardized
form. The following information can be read with a datasource:

    1. Station name
    2. Coordinate tuple (x,y,z)
    3. Uncertainty estimate of the coordinate (standard deviation)
    4. Weight [0;1]
    5. Timestamp

Source and target coordinate data is handled by different datasource instances. At
least one datasource is needed for both source and target data sources but more than
one can be supplied for each.

### Presenters

Presenters deliver the resulting estimated transformation parameters in sensible
formats. Parameters for a Helmert transformation might be presented as a
PROJ-string, a WKT2 description and a simple text representation. A grid based
transformation might result in a GTG file or a more complex transformation involving
several steps could be returned as a PROJ pipeline.

Presenters aren't limited to only presenting the estimated parameters. A presenter
can also return intermediate results, residuals and various other statistics relevant
to the transformation at hand.

### Operators

Operators are essential building blocks in the Transformo pipeline. All operators
have the ability to manipulate coordinates, generally in the sense of a geodetic
transformation. In addition operators *can* implement a method to derive
parameters for said coordinate operation. Most operators do, but not all.

So, operators have two principal modes of operation:

    1. Coordinate operations, as defined in the ISO 19111 terminology
    2. Estimating parameters for the coordinate operations

The abilities of a operator are determined by the methods that enheriting classes
implement. *All* Operator's must implement the `forward` method and they *can*
implement the `estimate` and `inverse` methods. If only the `forward` method is
implemented the operator will exist as a coordinate operation that can't
estimate parameters.

## For developers

This section is only relevant for developers working on the software.

### Installation

The installation process is similar to the one for regular users,
although the installed Python environment includes essential tools
for development as well:

```
mamba env create -f environment-dev.yml
mamba activate transformo-dev
pip install -e .
```

On top of setting up a Python environment and installing the package
developers also need to set up pre-commit scripts for git:

```
pre-commit install
```

### Code quality

We strive to keep the code quality in Transformo as high as possible. A number of
measures has been put into place to support this. They are described in the sections
below.

#### Tests

We do not accept code in the main-branch that is not sufficiently tested. The
Transformo code is tested in a Pytest test-suite. New code should come with
sufficient tests to ensure the long-term reliability of the software. All tests
should be passing before merging into the main branch.

#### Type annotations

Type annotations in Python improves readability of the code immensely and as an added
bonus it helps IDE's improve developer workflows. In addition, Transformo relies
heavily on the Pydantic framework which leverages type annotations to validate
incoming data.

MyPy is used to check that the types in Transformo are consistent throughout the
code. This can at times be a bit painful but it comes with the added benefit that it
can uncover errors in the code that normally wouldn't be noticed when relying on
Pythons dynamic nature.

#### Pydantic

Basic types in Transformo, such as `DataSource`'s and `Operators`'s, are Pydantic
`BaseModel`'s. Pydantic is used to validate user input in a simple way, in an
attempt to avoid problems caused by ill-formed input data. Transformo is built
on Pydantic's capability to serializee Python objects from a text source. In this
case the entire pipeline given in YAML format.

#### Black

The code is formatted using Black. Formatting by black can be turned off in sections
of the code where alternative formatting can be used to express the code in more
clear terms. The most likely case for this is where mathematical formulas are turned
into code, for example when setting up a rotation matrix.

#### Pre-commit hooks

Pre-commit hooks are used to enforce most of the above requirements to the code.

Remember to initialize the pre-commit hooks before committing your first code.
