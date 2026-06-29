// Water-vapour mass-fraction transport (Appendix A §2.3).
// eps dY/dt + div(U Y) - div(Deff grad Y) = -mDotAds/rhoG
// Deff = Dm/tau + 0.5 dp |U| / eps   (packed-bed axial dispersion closure)
{
    volScalarField Deff
    (
        "Deff",
        Dm/tau + 0.5*dp*mag(U)/eps
    );

    fvScalarMatrix YEqn
    (
        fvm::ddt(eps, Y)
      + fvm::div(phi, Y)
      - fvm::laplacian(Deff, Y)
     ==
      - mDotAds/rhoG
    );

    YEqn.relax();
    YEqn.solve();

    Y = max(min(Y, scalar(1)), scalar(0));   // bound the mass fraction
    Y.correctBoundaryConditions();
}
