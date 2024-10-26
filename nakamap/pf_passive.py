"""Map data from coil_vv_OP1.dat and coil_vv_OP2.dat files to a pf_passive IMAS IDS."""

import itertools
from pathlib import Path

import appdirs
import imaspy
import numpy as np
import pandas

path = Path(appdirs.user_data_dir("machine_description/coil_geometry"))
phase = "OP2"
pulse = {"OP1": 1001, "OP2": 1002}[phase]

# read pf_active row numbers from text file
filepath = path / f"coil_vv_{phase}.dat"
with open(filepath, "r") as file:
    coil_number = file.readline()
    _ = file.readline()
    row_numbers = file.readline().split()
skiprows = 3 + np.sum([int(nrow) for nrow in row_numbers])

# create pf_passive IDS
ids_factory = imaspy.IDSFactory()
pf_passive = ids_factory.pf_passive()
pf_passive.ids_properties.comment = f"Inital mapping of SST-1 pulse {pulse}."
pf_passive.ids_properties.homogeneous_time = 2  # constant data

# read pf_passive structure metadata
with open(filepath, "r") as file:
    filament_number = int(
        next(itertools.islice(file, skiprows, skiprows + 1)).split()[0]
    )
skiprows += 1
passive_data = pandas.read_csv(
    filepath,
    header=None,
    usecols=[0, 1, 2, 3, 4, 5],
    names=["nturn", "r", "z", "dr", "dz", "rho"],
    skiprows=skiprows,
    nrows=filament_number,
    sep=r"\s+",
)
skiprows += filament_number

# calculate coil resistance
passive_data["length"] = 2 * np.pi * passive_data["r"]
passive_data["area"] = passive_data["dr"] * passive_data["dz"]
passive_data["resistance"] = (
    passive_data["rho"] * passive_data["length"] / passive_data["area"]
)

# populate pf_passive ids
pf_passive.loop.resize(len(passive_data))
for i, (loop, (name, series)) in enumerate(
    zip(pf_passive.loop, passive_data.iterrows())
):

    loop.name = f"vv_{i}"
    loop.resistance = series.resistance
    loop.resistivity = series.rho
    loop.element.resize(1)
    element = loop.element[0]
    element.name = loop.name
    element.turns_with_sign = series.nturn
    element.area = series.area
    geometry = element.geometry
    geometry.geometry_type = 2  # rectangular
    rectangle = geometry.rectangle
    rectangle.r = series.r
    rectangle.z = series.z
    rectangle.width = series.dr
    rectangle.height = series.dz

# write ids to netCDF file
with imaspy.DBEntry(f"{path}/jt60sa_md_{phase}.nc", "a") as db_entry:
    db_entry.put(pf_passive)

# read ids from netCDF file
with imaspy.DBEntry(f"{path}/jt60sa_md_{phase}.nc", "r") as db_entry:
    pf_passive = db_entry.get("pf_passive")

# print result
imaspy.util.print_tree(pf_passive)

if __name__ == "__main__":

    from nova.imas.machine import PoloidalFieldPassive
    from nova.imas.dataset import IdsBase

    coilset = PoloidalFieldPassive(
        ids=pf_passive, filename=f"pf_passive_{phase}", **IdsBase.default_ids_attrs()
    )
    coilset.sloc["passive", "part"] = "vv"
    coilset.Loc["passive", "part"] = "vv"
    coilset.plot()
