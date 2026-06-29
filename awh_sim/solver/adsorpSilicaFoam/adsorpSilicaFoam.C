/*---------------------------------------------------------------------------*\
  adsorpSilicaFoam — Tier-2 high-fidelity solver for solar-regenerated
  silica-gel / water adsorption in a porous packed bed (LTE, single region).

  Implements Appendix A §2 directly:
    - U,p   : incompressible PIMPLE momentum + Darcy-Forchheimer porosity (fvOptions)
    - Y     : water-vapour mass fraction, with adsorption sink  -mDotAds/rhoG
    - T     : local-thermal-equilibrium energy, heat-of-adsorption source +dHads*mDotAds
    - q     : bed loading, semi-implicit Linear-Driving-Force  dq/dt = kLDF (q*-q)

  The single shared field mDotAds = (1-eps) rhoS dq/dt couples the Y, T sinks so
  they can never disagree in sign or magnitude (Appendix A §3.2 consistency rule).

  Low-Mach packed-bed flow: gas density treated constant (incompressible momentum);
  the gas-phase continuity mass change is small vs convective flux (Appendix A §2.1)
  and is accounted for through the Y sink integral, which equals the q uptake.
\*---------------------------------------------------------------------------*/

#include "fvCFD.H"
#include "pimpleControl.H"

// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //

int main(int argc, char *argv[])
{
    #include "setRootCase.H"
    #include "createTime.H"
    #include "createMesh.H"

    pimpleControl pimple(mesh);

    #include "createFields.H"

    Info<< "\nStarting time loop\n" << endl;

    while (runTime.loop())
    {
        Info<< "Time = " << runTime.timeName() << nl << endl;

        // --- pressure-velocity (momentum) ---
        while (pimple.loop())
        {
            #include "UEqn.H"
            #include "pEqn.H"
        }

        // --- adsorption update: q, qStar, kLDF, mDotAds (shared) ---
        #include "adsorptionUpdate.H"

        // --- transported scalars driven by the shared mDotAds ---
        #include "YEqn.H"
        #include "TEqn.H"

        runTime.write();

        Info<< "  max(T) = " << max(T).value()
            << " K   mean(q) = " << q.weightedAverage(mesh.V()).value()
            << " kg/kg   ExecutionTime = " << runTime.elapsedCpuTime() << " s"
            << nl << endl;
    }

    Info<< "End\n" << endl;
    return 0;
}

// ************************************************************************* //
