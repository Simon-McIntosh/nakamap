"""Map data from coil_vv_OP1.dat and coil_vv_OP2.dat files to a wall IMAS IDS."""

import itertools
from pathlib import Path

import appdirs
import imaspy
import numpy as np
import pandas

path = Path(appdirs.user_data_dir("machine_description/coil_geometry"))
phase = "OP1"
pulse = {"OP1": 1001, "OP2": 1002}[phase]

# create pf_active IDS
ids_factory = imaspy.IDSFactory()
wall = ids_factory.wall()
wall.ids_properties.comment = f"Inital mapping of SST-1 pulse {pulse}."
wall.ids_properties.homogeneous_time = 2  # constant data

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
skiprows += 1
wall_data = pandas.read_csv(
    filepath,
    header=None,
    usecols=[0, 1],
    names=["r", "z"],
    skiprows=skiprows,
    nrows=segment_number,
    sep=r"\s+",
)
skiprows += segment_number

# populate wall ids
wall.description_2d.resize(1)
wall.description_2d[0].vessel.unit.resize(1)
centerline = wall.description_2d[0].vessel.unit[0].annular.centreline
centerline.r = wall_data["r"]
centerline.z = wall_data["z"]
imaspy.util.inspect(wall.description_2d[0].vessel.unit[0].annular.centreline)

# write ids to netCDF file
with imaspy.DBEntry(f"{path}/jt60sa_md_{phase}.nc", "a") as db_entry:
    db_entry.put(wall)

# read ids from netCDF file
with imaspy.DBEntry(f"{path}/jt60sa_md_{phase}.nc", "r") as db_entry:
    wall = db_entry.get("wall")


# print result
imaspy.util.print_tree(wall)

if __name__ == "__main__":

    from nova.imas.machine import Wall
    from nova.imas.dataset import IdsBase

    coilset = Wall(ids=wall, filename=f"wall_{phase}", **IdsBase.default_ids_attrs())
    coilset.plot()
