// Incompressible momentum predictor with in-solver Darcy-Forchheimer (Ergun)
// porous resistance (kinematic form, Appendix A §2.2; coefficients validated in V2):
//   S = -(nu*dDarcy + 0.5*fForch*|U|) U   [m/s^2]
volScalarField poro
(
    "poro",
    nu*dDarcy + 0.5*fForch*mag(U)
);

fvVectorMatrix UEqn
(
    fvm::ddt(U)
  + fvm::div(phi, U)
  - fvm::laplacian(nu, U)
  + fvm::Sp(poro, U)
);

UEqn.relax();

if (pimple.momentumPredictor())
{
    solve(UEqn == -fvc::grad(p));
}
