# Re-plot

*a.k.a. How did I create that plot again 🤔*

-----

| `Python` | `matplotlib` | `git` |
|----------|--------------|-------|

-----

Did you ever want to recreate an old plot, changing just a small bit, but didn't manage because ...

* ... wait, which script did I use to create that plot?
* ... wait, what arguments did I pass to that script?
* ... wait, what version of all involved libraries did I use?
* ... wait, what environment variables were set at that time?
* ... wait, what is the correct version of the data files?
* ... wait, where did all the data files go?
* ...

This project aims to solve (most of) these problems and make plots fully reproducible at any time later in history.

## Concept

The approach relies on two aspects, *metadata* and *capturing*.

* **Metadata** is all the information that's addressed by the above questions, such as library versions, command line arguments, environment variables, etc.
* **Capturing** describes the way in which the metadata is stored together with the image.

The current version of `replot` saves the following metadata as the `UserComment` [Exif](https://en.wikipedia.org/wiki/Exif) tag together with the image (as a JSON dictionary):

* the current working directory
* script file path relative to repository root
* command line arguments
* environment variables
* version of all packages in the current virtual environment
* a snapshot of `matplotlib.rcParams`
* current commit hash

## How does it work?

All you need to do is `import replot` somewhere at the top of your script and then save your figures via the matplotlib [`Figure.savefig`](https://matplotlib.org/stable/api/figure_api.html#matplotlib.figure.Figure.savefig) method. Behind the scenes, `replot` patches this method in order to add the metadata information.

### File dependencies

`replot` monitors dependencies on external files by intercepting the following function calls:

* [builtin `open`](https://docs.python.org/3/library/functions.html#open)
* [`pandas.read_csv`](https://pandas.pydata.org/docs/reference/api/pandas.read_csv.html)
* [`numpy.load`](https://numpy.org/doc/stable/reference/generated/numpy.load.html) and [`numpy.loadtxt`](https://numpy.org/doc/stable/reference/generated/numpy.loadtxt.html)

Data that is accessed in different ways won't be added to the list of dependencies. Custom data loaders can be registered for monitoring via `replot.monitor`.

In addition, it counts the main script as well as any other imported custom modules as file dependencies.

If any of the file dependencies is not part of the git repository or if it contains unsaved changes, `replot` will refuse to create a new image via `Figure.savefig`. Instead it will print a warning which informs about the unsaved file dependencies. This warning can be suppressed via `from replot import nowarn`. A typical workflow would be to repeatedly view the plot via `plt.show()`, then commit all the changes and then running the script again will also create the plot image.

## How to view the data?

The `replot` package can be used to print the metadata in JSON format by passing the image file path as a command line argument or
by passing the `User Comment` field of the Exif data via stdin; for example:

```
python -m replot test.png
exiftool -UserComment test.png | python -m replot
```

This will print all metadata information, however typically the `commit_hash` field is sufficient,
given that `replot` enforces putting all file dependencies under version control before a figure can be saved.
