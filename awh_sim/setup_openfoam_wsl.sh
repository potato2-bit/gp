#!/usr/bin/env bash
# OpenFOAM install for the awh_sim high-fidelity (Tier 2) CFD.
# Requires sudo — RUN THIS YOURSELF in a WSL Ubuntu terminal (it will prompt for your
# password). Claude cannot run it: sudo needs a password it does not have.
#
#   wsl                       # open the Ubuntu shell, then:
#   bash "/mnt/c/Users/rizk/Desktop/GRADUATION PROJECT/awh_sim/setup_openfoam_wsl.sh"
#
set -e

echo ">> Adding the ESI OpenFOAM apt repo (openfoam.com)..."
curl -fsSL https://dl.openfoam.com/add-debian-repo.sh | sudo bash

echo ">> Installing openfoam2406-default..."
sudo apt-get update
sudo apt-get install -y openfoam2406-default
# Optional: GNU parallel for DoE batching. NOT required — run_doe.sh defaults to xargs -P.
#   sudo apt-get install -y parallel

echo ">> Sourcing OpenFOAM in ~/.bashrc..."
grep -q 'openfoam2406/etc/bashrc' ~/.bashrc \
  || echo 'source /usr/lib/openfoam/openfoam2406/etc/bashrc' >> ~/.bashrc

echo ">> Done. Open a new shell (or 'source /usr/lib/openfoam/openfoam2406/etc/bashrc'),"
echo "   then verify:  blockMesh -help  &&  echo OK"
