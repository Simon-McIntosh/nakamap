"""Map data from coil_vv_OP1.dat and coil_vv_OP2.dat files to a magnetics IMAS IDS."""

import itertools
from pathlib import Path

import appdirs
import imaspy
import numpy as np
import pandas
import xarray

from nova.graphics.plot import Plot2D

path = Path(appdirs.user_data_dir("machine_description/coil_geometry"))
phase = "OP2"
pulse = {"OP1": 1001, "OP2": 1002}[phase]

# create pf_active IDS
ids_factory = imaspy.IDSFactory()
magnetics = ids_factory.magnetics()
magnetics.ids_properties.comment = f"Inital mapping of SST-1 pulse {pulse}."
magnetics.ids_properties.homogeneous_time = 2  # constant data

# read pf_active metadata
filepath = path / f"coil_vv_{phase}.dat"
with open(filepath, "r") as file:
    _ = file.readline()
    _ = file.readline()
    row_numbers = file.readline().split()
skiprows = 3 + np.sum([int(nrow) for nrow in row_numbers])

# read pf_passive structure metadata
with open(filepath, "r") as file:
    filament_number = int(
        next(itertools.islice(file, skiprows, skiprows + 1)).split()[0]
    )
skiprows += 1 + filament_number

# read first wall contour
with open(filepath, "r") as file:
    segment_number = int(
        next(itertools.islice(file, skiprows, skiprows + 1)).split()[0]
    )
skiprows += 1 + segment_number

# read vessel contours
with open(filepath, "r") as file:
    _ = next(itertools.islice(file, skiprows, skiprows + 1))
    contour_number = int(file.readline().split()[0])

skiprows += 2

contour_data = pandas.read_csv(
    filepath,
    header=None,
    usecols=[0, 1, 2, 3, 5],
    names=["r0", "z0", "r1", "z1", "part"],
    skiprows=skiprows,
    nrows=contour_number,
    sep=r"\s+",
)
contour_data.ffill(inplace=True)
contour_data.loc[:, "part"] = [
    part[2:].replace(",", "") for part in contour_data.loc[:, "part"]
]

skiprows += contour_number

# read flux loops from file
with open(filepath, "r") as file:
    loop_number = int(next(itertools.islice(file, skiprows, skiprows + 1)).split()[0])
skiprows += 1
loop_data = pandas.read_csv(
    filepath,
    header=None,
    usecols=[0, 1],
    names=["r", "z"],
    skiprows=skiprows,
    nrows=loop_number,
    sep=r"\s+",
)
skiprows += loop_number

# read magnetic probes from file
with open(filepath, "r") as file:
    probe_number = int(next(itertools.islice(file, skiprows, skiprows + 1)).split()[0])
skiprows += 1

probe_data = pandas.read_csv(
    filepath,
    header=None,
    usecols=[0, 1, 2],
    names=["r", "z", "theta"],
    skiprows=skiprows,
    nrows=probe_number,
    sep=r"\s+",
)
skiprows += probe_number

# fill magnetics IDS
magnetics.flux_loop.resize(loop_number)
for i, (flux_loop, (_, position)) in enumerate(
    zip(magnetics.flux_loop, probe_data.iterrows())
):
    flux_loop.name = f"flux_loop_{i}"
    flux_loop.type.name = "poloidal_flux"
    flux_loop.type.index = 1
    flux_loop.type.description = "Poloidal flux loop"
    flux_loop.position.resize(1)
    flux_loop.position[0].r = position.r
    flux_loop.position[0].z = position.z
    flux_loop.position[0].phi = 0
    flux_loop.area = np.pi * position.r**2

'''
# fill poloidal probes
magnetics.b_field_pol_probe.resize(probe_number)
for i, (b_probe, (_, position)) in enumerate(
    zip(magnetics.b_field_pol_probe, probe_data.iterrows())
):
    b_probe.name = f"b_field_pol_probe_{i}"
    b_probe.type.name = "poloidal_flux"
    b_probe.type.index = 1
    b_probe.type.description = "Poloidal flux loop"
    b_probe.position.resize(1)
    b_probe.position[0].r = position.r
    b_probe.position[0].z = position.z
    b_probe.poloidal_angle = position.theta
    b_probe.position[0].phi = 0
    b_probe.area = np.pi * position.r**2
"""
'''

# print result
imaspy.util.print_tree(magnetics)

# write ids to netCDF file
with imaspy.DBEntry(f"{path}/jt60sa_md_{phase}.nc", "a") as db_entry:
    db_entry.put(magnetics)

# read ids from netCDF file
with imaspy.DBEntry(f"{path}/jt60sa_md_{phase}.nc", "r") as db_entry:
    magnetics = db_entry.get("magnetics")

# store loop data to netCDF file
contour_data.to_xarray().to_netcdf(path / f"contour_data_{phase}.nc")
loop_data.to_xarray().to_netcdf(path / f"loop_data_{phase}.nc")
probe_data.to_xarray().to_netcdf(path / f"probe_data_{phase}.nc")

# load loop data from netCDF file
contour_data = xarray.open_dataset(path / f"contour_data_{phase}.nc").to_pandas()
loop_data = xarray.open_dataset(path / f"loop_data_{phase}.nc").to_pandas()
probe_data = xarray.open_dataset(path / f"probe_data_{phase}.nc").to_pandas()


if __name__ == "__main__":

    axes = Plot2D().get_axes()
    for part in contour_data.part.unique():
        frame = contour_data.loc[contour_data.part == part]
        loop = np.append(
            frame.loc[:, ["r1", "z1"]].values,
            frame.loc[:, ["r1", "z1"]].values[:1],
            axis=0,
        )
        axes.plot(*loop.T, color="gray")

    axes.plot(loop_data.r, loop_data.z, marker="X", linestyle="", color="gray")
    axes.plot(probe_data.r, probe_data.z, marker="o", linestyle="", color="gray")
