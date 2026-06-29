// LTE energy equation (Appendix A §2.4).
// d/dt[(rho cp)_eff T] + rhoG cpG div(U T) - div(k_eff grad T) = dHads * mDotAds
{
    volScalarField rhoCpEff
    (
        "rhoCpEff",
        eps*rhoG*cpG + (1.0 - eps)*rhoS*(cpS + q*cpW)
    );

    // effective conductivity is spatially uniform (LTE, constant solid/gas k)
    dimensionedScalar kEff("kEff", eps*kG + (1.0 - eps)*kS);

    fvScalarMatrix TEqn
    (
        fvm::ddt(rhoCpEff, T)
      + rhoG*cpG*fvm::div(phi, T)
      - fvm::laplacian(kEff, T)
     ==
        dHads*mDotAds
    );

    TEqn.relax();
    TEqn.solve();
    T.correctBoundaryConditions();
}
