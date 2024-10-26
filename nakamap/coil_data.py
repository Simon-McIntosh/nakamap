"""Read JT-60SA geometry from IDSs and plot using the nova code."""

from pathlib import Path

import appdirs
import imaspy
import numpy as np
import xarray

from nova.graphics.plot import Plot2D

path = Path(appdirs.user_data_dir("machine_description/coil_geometry"))
phase = "OP2"
pulse = {"OP1": 1001, "OP2": 1002}[phase]


# read ids from netCDF file
with imaspy.DBEntry(f"{path}/jt60sa_md_{phase}.nc", "r") as db_entry:
    pf_active = db_entry.get("pf_active")
    pf_passive = db_entry.get("pf_passive")
    wall = db_entry.get("wall")


if __name__ == "__main__":

    from nova.imas.machine import PoloidalFieldActive, PoloidalFieldPassive, Wall
    from nova.imas.dataset import IdsBase

    coilset = PoloidalFieldActive(
        ids=pf_active, filename=f"pf_active_{phase}", **IdsBase.default_ids_attrs()
    )
    coilset.plot()
    coilset.frame.vtkgeo.generate_vtk()
    coilset += PoloidalFieldPassive(
        ids=pf_passive, filename=f"pf_passive_{phase}", **IdsBase.default_ids_attrs()
    )
    coilset.plot()
    coilset.frame.vtkgeo.generate_vtk()
    coilset += Wall(ids=wall, filename=f"wall_{phase}", **IdsBase.default_ids_attrs())

    coilset.sloc["passive", "part"] = "vv"
    coilset.Loc["passive", "part"] = "vv"

    # plot result
    coilset.plot()

    # TODO we shoed access this data via an IDS
    # load loop data from netCDF file
    contour_data = xarray.open_dataset(path / f"contour_data_{phase}.nc").to_pandas()
    loop_data = xarray.open_dataset(path / f"loop_data_{phase}.nc").to_pandas()
    probe_data = xarray.open_dataset(path / f"probe_data_{phase}.nc").to_pandas()

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
