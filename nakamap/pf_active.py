"""Map data from coil_vv_OP1.dat and coil_vv_OP2.dat files to a pf_active IMAS IDS."""

import itertools
from pathlib import Path

import appdirs
import imaspy
import numpy as np
import pandas

path = Path(appdirs.user_data_dir("machine_description/coil_geometry"))
phase = "OP2"
pulse = {"OP1": 1001, "OP2": 1002}[phase]

# create pf_active IDS
ids_factory = imaspy.IDSFactory()
pf_active = ids_factory.pf_active()
pf_active.ids_properties.comment = f"Inital mapping of SST-1 pulse {pulse}."
pf_active.ids_properties.homogeneous_time = 2  # constant data

# read coil metadata from text file
filepath = path / f"coil_vv_{phase}.dat"
with open(filepath, "r") as file:
    coil_number = file.readline()
    _ = file.readline()
    row_numbers = file.readline().split()
    coil_names = []
    for nrows in [int(number) for number in row_numbers]:
        coil_names.append(file.readline().split()[-1])
        _ = next(itertools.islice(file, nrows - 2, nrows - 1))

# read coil geometries from text file
skiprows = 3
coil_data = {}
for name, nrows in zip(coil_names, [int(number) for number in row_numbers]):
    coil_data[name] = pandas.read_csv(
        filepath,
        header=None,
        usecols=[0, 1, 2, 3, 4],
        names=["nturn", "r", "z", "dr", "dz"],
        skiprows=skiprows,
        nrows=nrows,
        sep=r"\s+",
    )
    skiprows += nrows

# process data and populate pf_active ids
pf_active.coil.resize(len(coil_data))
for coil, (name, data) in zip(pf_active.coil, coil_data.items()):
    patch_area = data["dr"] * data["dz"]
    area = np.sum(patch_area)
    r = np.sum(data["r"] * patch_area) / area
    z = np.sum(data["z"] * patch_area) / area
    dr = np.max(data["r"] + data["dr"] / 2) - np.min(data["r"] - data["dr"] / 2)
    dz = np.max(data["z"] + data["dz"] / 2) - np.min(data["z"] - data["dz"] / 2)
    nturn = np.sum(data["nturn"])
    part = {"CS": "cs", "EF": "pf", "FP": "ivc"}[name[:2]]

    coil.name = name
    coil.resistance = 0
    coil.element.resize(1)
    element = coil.element[0]
    element.name = name
    element.turns_with_sign = nturn
    element.area = area
    geometry = element.geometry
    geometry.geometry_type = 2  # rectangular
    rectangle = geometry.rectangle
    rectangle.r = r
    rectangle.z = z
    rectangle.width = dr
    rectangle.height = dz

# write ids to netCDF file
with imaspy.DBEntry(f"{path}/jt60sa_md_{phase}.nc", "w") as db_entry:
    db_entry.put(pf_active)

# read ids from netCDF file
with imaspy.DBEntry(f"{path}/jt60sa_md_{phase}.nc", "r") as db_entry:
    pf_active = db_entry.get("pf_active")

# print result
imaspy.util.print_tree(pf_active)

if __name__ == "__main__":

    from nova.imas.machine import PoloidalFieldActive
    from nova.imas.dataset import IdsBase

    coilset = PoloidalFieldActive(
        ids=pf_active, filename=f"pf_active_{phase}", **IdsBase.default_ids_attrs()
    )
    coilset.plot()
