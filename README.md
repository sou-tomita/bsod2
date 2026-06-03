# bsod2 <!-- omit in toc -->

<p>
<img src="https://img.shields.io/pypi/v/bsod2">
<a href="https://github.com/sotomita/bsod2/actions/workflows/publish.yml"><img src="https://github.com/sotomita/bsod2/actions/workflows/publish.yml/badge.svg"></a>
<img src="https://img.shields.io/pypi/dm/bsod2.svg?label=PyPI%20downloads">
<img src="https://img.shields.io/github/license/sotomita/bsod2">
<img src="https://img.shields.io/github/languages/code-size/sotomita/bsod2">
<img src="https://img.shields.io/pypi/pyversions/bsod2.svg?logo=python&logoColor=white">
</p>

BSoD2 (BalloonScope on Deck 2) is a command line interface and Python package for reading, processing, and plotting radiosonde data.

<p align="center">
<img src="https://raw.githubusercontent.com/sotomita/bsod2/master/docs/images/emagram.png" alt="emagram" width="200"/>
<img src="https://raw.githubusercontent.com/sotomita/bsod2/master/docs/images/trj2d.png" alt="RH 2D trajectory" width="200"/><br>
<img src="https://raw.githubusercontent.com/sotomita/bsod2/master/docs/images/trj3d_animation.gif" alt="RH 3D trajectory" width="400"/>
</p>

## Table of Contents <!-- omit in toc -->

- [Installation](#installation)
- [Usage](#usage)
  - [Command Line Interface](#command-line-interface)
  - [Python module](#python-module)
    - [Basic `Sondeset` construction and methods](#basic-sondeset-construction-and-methods)
    - [Accessors for individual data items](#accessors-for-individual-data-items)
    - [Get Number of profiles](#get-number-of-profiles)
    - [Save as CSV](#save-as-csv)
    - [Altitude or pressure interpolation](#altitude-or-pressure-interpolation)
    - [Interpolated and combined `xarray.Dataset`](#interpolated-and-combined-xarraydataset)
    - [plot emagram](#plot-emagram)
  - [Sample data and scripts](#sample-data-and-scripts)
  - [License](#license)

## Installation
This package can be installed from [PyPI](https://pypi.org/project/bsod2/).
```
pip install bsod2
```

## Usage
The only functionality provided by this package is the `bsod2.Sondeset` class, which retrieves radiosonde data ,performs quality control and plot a emagram.      
A simple usage guide in Japanese is available on Qiita: ([bsod2 ラジオゾンデ観測データ品質管理ツール](https://qiita.com/aoitomita/private/302a19c4236819f310e9)).

### Command Line Interface
`bsod2` commannd performs on quality control.
```
$ bsod2 ./sample/Seisuimaru2407/raw_data ./output
 25%|███████              2/8 [00:01<00:03,  1.78it/s]
```
The first positional argument specifies the path to the input data file or directory.  
The second one specifies the path to the output directory.  
For more information, run: 
```bsod2 --help```

### Python module
#### Basic `Sondeset` construction and methods

Initialize the class with the file path to the raw data.
```
from pathlib import Path
from bsod2 import Sondeset

ss = Sondeset(Path("Seisuimaru2407/raw_data/F2024061806S1101771.CSV"))
print(ss)
>>> N=1, sonde_no=["1101771"]
```

If a directory path is given, all sonde data files (`F*S*.CSV`) in that directory are loaded.
```
ss = Sondeset(Path("Seisuimaru2407/raw_data"))
print(ss)
>>> N=8, sonde_no=["1101771", "1101323", "1101386", "1101322", "1101327", "1101772", "1101388", "1101326"]
```

Individual data items can be accessed by indexing.
```
print(ss[0])
>>> Sonde(sonde_no=1101771, launch_time=2024-06-18 06:01:42, product_name=iMS-100 , num_records=4174)
```

#### Accessors for individual data items
The following accessors can be used to access individual data items.   
Most accessors return values with `metpy.units.units` attached.

| Accessor | units | Description | Example |
|----------|-------------|---------| ---------|
|`df`|`None`| quality-controlled `pandas.DataFrame`|`ss[0].df`|
|`time`|`None`|Time|`ss[0].time`|
|`lat`|`units("deg")`| Latitude|`ss[0].lat`|
|`lon`|`units("deg")`| Longitude|`ss[0].lon`|
|`x`|`units("m")`| X-displacement from the launch point|`ss[0].x`|
|`y`|`units("m")`| Y-displacement from the launch point|`ss[0].y`|
|`z`| ```units("m")```  | Altitude | `ss[0].z` |
|`p`| ```units("hPa")```  | Pressure | `ss[0].p` |
|`t`| ```units("degC")```| Temperature | `ss[0].tss` |
|`rh`|```units("percents")```| Relative humidity | `ss[0].rh` |
|`td`|`units("degC")`|dewpoint|`ss[0].td`|
|`wd`|```units("deg")```| Wind direction | `ss[0].wd` |
|`ws`| ```units("m/s")```| Wind speed | `ss[0].ws` |
|`u`| ```units("m/s")```| U-component wind | `ss[0].u` |
|`v`| ```units("m/s")```| V-component wind | `ss[0].v` |


#### Get Number of profiles
`len` function can be used to get number of profiles contained in  `Sondeset`.
```
len(ss)
>>> 8
```

#### Save as CSV
Save the quality-controlled DataFrame as a CSV file to the specified file path using the `save_df` method.
```
ss[0].save_df(Path("output.csv"))
```

#### Altitude or pressure interpolation
Interpolate linearly onto an evenly spaced grid in pressure(`"p"`) or altitude(`"z"`) using the `interp` argument.
```
ss = Sondeset(DIR_PATH,interp="p")
```
By default, the interpolated pressure axis ranges from 50 to 1,100 hPa at 1 hPa intervals, or the height axis ranges from 0 m to 20,000 m at 10 m intervals.   
Values outside the original data range are filled with NaN. The range and resolution of the interpolation axes can be specified using the following arguments.

| Argument| Description                                                                 | Default |
|---------------|-----------------------------------------------------------------------------|---------|
|`interp`| Name of the interpolation axis. If `None`, interpolation is not performed.|`None`|
| `interp_pmin` | Minimum value of the interpolated pressure axis (hPa)                       | 50     |
| `interp_pmax` | Maximum value of the interpolated pressure axis (hPa)                       | 1100    |
| `interp_dp`   | Step size of the interpolated pressure axis (hPa)                           | 1       |
| `interp_zmin` | Minimum value of the interpolated height axis (m)                           | 0       |
| `interp_zmax` | Maximum value of the interpolated height axis (m)                           | 20000   |
| `interp_dz`   | Step size of the interpolated height axis (m)                               | 10      |

#### Interpolated and combined `xarray.Dataset`
`Sondeset.ds` provides access to an `xarray.Dataset` containing interpolated and combined radiosonde data.
```
ss = Sondeset(Path("Seisuimaru2407/raw_data", interp="z"))
print(ss.ds)
>>> 
xarray.Dataset> Size: 785kB
Dimensions:      (n: 8, z: 2001)
Coordinates:
  * n            (n) <U7 224B '1101771' '1101323' ... '1101388' '1101326'
  * z            (z) float64 16kB 0.0 10.0 20.0 ... 1.998e+04 1.999e+04 2e+04
Data variables:
    p            (n, z) float64 128kB nan 1.007e+03 1.005e+03 ... nan nan nan
    tmp          (n, z) float64 128kB nan 18.76 18.93 19.0 ... nan nan nan nan
    wd           (n, z) float64 128kB nan 270.4 252.9 250.7 ... nan nan nan nan
    ws           (n, z) float64 128kB nan 2.426 2.09 2.16 ... nan nan nan nan
    rh           (n, z) float64 128kB nan 89.21 89.78 90.21 ... nan nan nan nan
    launch_time  (n) datetime64[us] 64B 2024-06-18T06:01:42 ... 2024-06-18T14...
    time         (n, z) datetime64[ns] 128kB 2024-06-18T06:01:42 ... 2024-06-...
```

#### plot emagram
`plot_emagram` is a method for plotting a temperature emagram.
```
ss[0].plot_emagram(save_dir=Path("./"))
```

### Sample data and scripts
[Sample data](https://github.com/sotomita/bsod2/tree/master/sample/Seisuimaru2407) was observed in Seisui-maru 2407 cruise
(2024年度　三重大学　陸海空・環境科学実習).  

See [sample/sample.md](sample/sample.md) for sample scripts.


### License
This project is distributed under the terms of the GNU General Public License, Version 3 (GPLv3).  
See the [LICENSE](LICENSE) file for details.