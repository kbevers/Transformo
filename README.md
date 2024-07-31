# Transformo

Transformo is a generalized software package for estimating geodetic transformation
parameters and models.

The problem Transformo tries to solve can be presented on the idealized form

```
T = M(p, S)
```

Where `S` and `T` are the source and target coordinates, `M` is a transformation model
and `p` is the parameters for the chosen model.

The real world is rarely simple so a more realistic form would be

```
T = M(p, S) + R
```

Where `R` is the transformation residuals.

The primary function of Transformo is to provide a set of parameters `p` that minimizes
the residual `R`. In some cases that might involve a transformation model consisting
of several steps:

```
T = M3(p3, M2(p2, M1(p1, S))) + R
```

Transformo seeks to provide a framework that lets the user focus on determining the
best transformation model while removing the burden of reading coordinate data from
various sources and providing the resulting parameters in standardized formats for
ease of use in end-user software.

## Rationale

The rationale behind Transformo is to create a framework that removes the tedious work
of reading input data and presenting the results after transformation parameters has
been determined. In particular, this approch is meant to be a service to researchers
that develop new for methods geodetic coordinate transformations, as they can focus on
the core algorithms and not the supporting scaffolding.

## Installation

Clone the repository from GitHub and run the following commands in the root:

```
mamba env create -f environment.yml
pip install -e .
```

## Use Cases

* Estimate a 7-parameter Helmert transformation
* Derive the next iteration of the NKG Transformations
* Adjust a geoid model to a height system
* ...

## Architecture

The overall architecture consists of a pipeline on the form

```
DATASOURCE_1                                                        WRITER_1

DATASOURCE_2                                                        WRITER_2

DATASOURCE_3   -> ESTIMATOR_1 -> ESTIMATOR_2 -> ... > ESTIMATOR_N > WRITER_3

    ...                                                              ...

DATASOURCE_N                                                        WRITER_4
```

where *datasources* gathers sets of source and target coordinates and velocities and assembles them
in a standardized internal form and *writers* presents the derived transformation model in
standardized formats.

The *estimators* derive parameters for selected transformation techniques, for instance a Helmert
transformation. In case of several chained estimators the later steps are presented with the
residuals of the earlier transformation estimate for which the current estimator can attemt to
reduce even further using a different transformations technique.

### DataSources

DataSources should consume data from a single data source and provide it on a standardized form.
A DataSource should be able to read the following information from a datasource:

    1. Station name
    2. Coordinate tuple (x,y,z)
    3. Uncertainty estimate of the coordinate
    4. Weight [0;1]
    5. Timestamp

Source and target coordinate data is handled by different DataSource instances. At least one DataSource is needed
for both source and target data sources but more than one can be supplied for each.

### Writers

Writers deliver the resulting estimated transformation parameters in sensible formats. Parameters
for a Helmert transformation might be presented as a PROJ-string, a WKT2 description and a simple
text representation. A grid based transformation might result in a GTG file or a more complex
transformation involving several steps could be returned as a PROJ pipeline.

### Estimators

## For developers

### Code quality

We strive to keep the code quality in Transformo as high as possible. A number of measures has been put into place
to support this.

#### Tests

We do not accept code in the main-branch that is not sufficiently tested. The Transformo code is testing in a
Pytest test-suite.

#### Type hints

Type hinting in Python improves readability of the code immensely and as an added bonus it helps IDE's improve
developer workflows. MyPy is used to check that the types in Transformo are consistent throughout the code. This
can at times be a bit painful but it comes with the added benefit that it can uncover errors in the code that
normally wouldn't be noticed when relying on Pythons dynamic nature.

#### Pydantic

Basic types in Transformo, such as `DataSource`'s and `Estimators`'s, are Pydantic `BaseModel`'s. Pydantic is used
to validate user input in a simple way, in an attempt to avoid problems caused by ill-formed input data.

#### Black

The code is formatted using Black. Formatting by black can be turned off in sections of the code where alternative
formatting can be used to express the code in more clear terms. The most likely case for this is where mathematical
formulas are turned into code, for example when setting up a rotation matrix.

#### Pre-commit hooks

Pre-commit hooks are used to enforce most of the above requirements to the code.
