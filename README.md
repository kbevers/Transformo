# Transformo

Transformo is a generalized software package for estimating geodetic transformation
parameters and models.

The problem that Transformo tries to solve can be presented on the idealized form

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
READER_1                                                        WRITER_1

READER_2                                                        WRITER_2

READER_3   -> ESTIMATOR_1 -> ESTIMATOR_2 -> ... > ESTIMATOR_N > WRITER_3

    ...                                                              ...

READER_N                                                        WRITER_4
```

where *readers* gathers sets of source and target coordinates and velocities and assembles them
in a standardized internal form and *writers* presents the derived transformation model in
standardized formats.

The *estimators* derive parameters for selected transformation techniques, for instance a Helmert
transformation. In case of several chained estimators the later steps are presented with the
residuals of the earlier transformation estimate for which the current estimator can attemt to
reduce even further using a different transformations technique.

### Readers

Readers should consume data from a single data source and provide it on a standardized form.
A reader should be able to read the following information from data-source:

    1. Station name
    2. Coordinate tuple (x,y,z)
    3. Uncertainty estimate of the coordinate
    4. Weight [0;1]
    5. Timestamp

Source and target coordinate data is handled by different readers. At least one reader is needed
for both source and target data sources but more than one can be supplied for each.

### Writers

Writers deliver the resulting estimated transformation parameters in sensible formats. Parameters
for a Helmert transformation might be presented as a PROJ-string, a WKT2 description and a simple
text representation. A grid based transformation might result in a GTG file or a more complex
transformation involving several steps could be returned as a PROJ pipeline.

### Estimators
