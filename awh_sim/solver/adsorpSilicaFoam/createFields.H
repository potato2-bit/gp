Info<< "Reading transportProperties\n" << endl;
IOdictionary transportProperties
(
    IOobject
    (
        "transportProperties",
        runTime.constant(),
        mesh,
        IOobject::MUST_READ_IF_MODIFIED,
        IOobject::NO_WRITE
    )
);
dimensionedScalar nu("nu", dimViscosity, transportProperties);

Info<< "Reading field p\n" << endl;
volScalarField p
(
    IOobject("p", runTime.timeName(), mesh, IOobject::MUST_READ, IOobject::AUTO_WRITE),
    mesh
);

Info<< "Reading field U\n" << endl;
volVectorField U
(
    IOobject("U", runTime.timeName(), mesh, IOobject::MUST_READ, IOobject::AUTO_WRITE),
    mesh
);

#include "createPhi.H"

label pRefCell = 0;
scalar pRefValue = 0.0;
setRefCell(p, pimple.dict(), pRefCell, pRefValue);
mesh.setFluxRequired(p.name());

// ---------------------------------------------------------------------------
// adsorption / bed properties
// ---------------------------------------------------------------------------
Info<< "Reading adsorptionProperties\n" << endl;
IOdictionary adsProps
(
    IOobject
    (
        "adsorptionProperties",
        runTime.constant(),
        mesh,
        IOobject::MUST_READ_IF_MODIFIED,
        IOobject::NO_WRITE
    )
);

dimensionedScalar eps  ("eps",   dimless,                       adsProps);
dimensionedScalar rhoG ("rhoG",  dimDensity,                    adsProps);
dimensionedScalar rhoS ("rhoS",  dimDensity,                    adsProps);
dimensionedScalar cpG  ("cpG",   dimensionSet(0,2,-2,-1,0,0,0), adsProps);
dimensionedScalar cpS  ("cpS",   dimensionSet(0,2,-2,-1,0,0,0), adsProps);
dimensionedScalar cpW  ("cpW",   dimensionSet(0,2,-2,-1,0,0,0), adsProps);
dimensionedScalar kG   ("kG",    dimensionSet(1,1,-3,-1,0,0,0), adsProps);
dimensionedScalar kS   ("kS",    dimensionSet(1,1,-3,-1,0,0,0), adsProps);
dimensionedScalar Dm   ("Dm",    dimViscosity,                  adsProps);
dimensionedScalar tau  ("tau",   dimless,                       adsProps);
dimensionedScalar dp   ("dp",    dimLength,                     adsProps);
dimensionedScalar dHads("dHads", dimensionSet(0,2,-2,0,0,0,0),  adsProps);
// Ergun Darcy-Forchheimer coefficients (Appendix A §2.2; validated in V2)
dimensionedScalar dDarcy("dDarcy", dimensionSet(0,-2,0,0,0,0,0), adsProps);
dimensionedScalar fForch("fForch", dimensionSet(0,-1,0,0,0,0,0), adsProps);

// scalar constants used only in the per-cell adsorption ODE
const scalar Mw   = adsProps.get<scalar>("Mw");     // kg/mol water
const scalar Mair = adsProps.get<scalar>("Mair");   // kg/mol dry air
const scalar Ptot = adsProps.get<scalar>("Ptot");   // Pa total pressure
const scalar Ds0  = adsProps.get<scalar>("Ds0");    // m2/s
const scalar Ea   = adsProps.get<scalar>("Ea");     // J/mol
const scalar F0   = adsProps.get<scalar>("F0");     // - (15)
const scalar Rp   = adsProps.get<scalar>("Rp");     // m pellet radius
const scalar Rgas = adsProps.get<scalar>("Rgas");   // J/mol/K
const scalar T0K  = adsProps.get<scalar>("T0K");    // 273.15
// Tier-0 Sips isotherm (van't Hoff T-law): q* = qm (K Pv)^n / (1+(K Pv)^n)
const scalar qm_s   = adsProps.get<scalar>("qm_s");
const scalar Kref_s = adsProps.get<scalar>("Kref_s");   // 1/Pa at Tref
const scalar dHk_s  = adsProps.get<scalar>("dHk_s");    // J/mol (van't Hoff)
const scalar n0_s   = adsProps.get<scalar>("n0_s");
const scalar n1_s   = adsProps.get<scalar>("n1_s");     // 1/degC
const scalar Tref_C = adsProps.get<scalar>("Tref_C");   // 30 degC
const scalar epsV  = eps.value();
const scalar rhoSV = rhoS.value();
const scalar rhoGV = rhoG.value();

// ---------------------------------------------------------------------------
// transported / derived fields
// ---------------------------------------------------------------------------
Info<< "Reading field Y (vapour mass fraction)\n" << endl;
volScalarField Y
(
    IOobject("Y", runTime.timeName(), mesh, IOobject::MUST_READ, IOobject::AUTO_WRITE),
    mesh
);

Info<< "Reading field T\n" << endl;
volScalarField T
(
    IOobject("T", runTime.timeName(), mesh, IOobject::MUST_READ, IOobject::AUTO_WRITE),
    mesh
);

volScalarField q
(
    IOobject("q", runTime.timeName(), mesh, IOobject::READ_IF_PRESENT, IOobject::AUTO_WRITE),
    mesh,
    dimensionedScalar("q", dimless, 0.0)
);

volScalarField qStar
(
    IOobject("qStar", runTime.timeName(), mesh, IOobject::NO_READ, IOobject::AUTO_WRITE),
    mesh,
    dimensionedScalar("qStar", dimless, 0.0)
);

volScalarField kLDF
(
    IOobject("kLDF", runTime.timeName(), mesh, IOobject::NO_READ, IOobject::AUTO_WRITE),
    mesh,
    dimensionedScalar("kLDF", dimensionSet(0,0,-1,0,0,0,0), 0.0)
);

volScalarField mDotAds
(
    IOobject("mDotAds", runTime.timeName(), mesh, IOobject::NO_READ, IOobject::AUTO_WRITE),
    mesh,
    dimensionedScalar("mDotAds", dimensionSet(1,-3,-1,0,0,0,0), 0.0)
);
