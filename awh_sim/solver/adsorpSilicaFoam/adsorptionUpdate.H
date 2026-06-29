// Per-cell adsorption update (Appendix A §2.5-2.6, §3.3).
// Semi-implicit LDF:  q^{n+1} = (q^n + dt kLDF q*) / (1 + dt kLDF)  (unconditionally
// stable, exact for constant q*).  q* from the Hraiech 2025 adsorption correlation;
// RH from the local vapour mass fraction via the ideal-gas partial pressure.
{
    const scalar dt = runTime.deltaTValue();

    forAll(T, c)
    {
        const scalar Tc  = T[c];                                   // K
        const scalar Tc_C = Tc - T0K;                              // degC
        scalar Yc = Y[c];
        Yc = max(scalar(0), min(scalar(1), Yc));

        // vapour mole fraction -> partial pressure (ideal gas)
        const scalar denom = Yc/Mw + (1.0 - Yc)/Mair;
        const scalar xv = (denom > 0) ? (Yc/Mw)/denom : 0.0;
        const scalar Pv = max(xv*Ptot, scalar(0));                 // Pa

        // equilibrium loading q* — Tier-0 Sips with van't Hoff T-law.
        // Thermodynamically consistent: q*->0 as Pv->0 and q* falls with T, so it is
        // valid through regeneration (the raw Hraiech correlation is not, above ~33 C).
        const scalar invT  = 1.0/Tc - 1.0/(Tref_C + T0K);
        const scalar Ksips = Kref_s*Foam::exp(-dHk_s/Rgas*invT);   // 1/Pa
        // clamp the heterogeneity exponent to stay physical (0,1] when the linear
        // n(T) fit is extrapolated above its 27-44 C calibration to regeneration T
        scalar nsips = n0_s + n1_s*(Tc_C - 25.0);
        nsips = max(scalar(0.1), min(scalar(1.0), nsips));
        const scalar KP = Foam::pow(max(Ksips*Pv, scalar(0)), nsips);
        scalar qs = qm_s*KP/(1.0 + KP);
        qs = max(qs, scalar(0));

        // Chihara/Glueckauf LDF coefficient
        const scalar Ds = Ds0*Foam::exp(-Ea/(Rgas*Tc));
        const scalar kL = F0*Ds/Foam::sqr(Rp);

        const scalar qOld = q[c];
        const scalar qNew = (qOld + dt*kL*qs)/(1.0 + dt*kL);       // semi-implicit LDF
        scalar mDot = (1.0 - epsV)*rhoSV*(qNew - qOld)/dt;         // kg/m3/s (>0 adsorb)

        // conservation limiter: adsorption cannot remove more vapour than is locally
        // present this step (stops the Y>=0 clamp from creating water in the closed
        // box; rarely binds in flow-through, where convection replenishes Y).
        const scalar mDotMax = epsV*rhoGV*Yc/dt;
        if (mDot > mDotMax) mDot = mDotMax;

        qStar[c]   = qs;
        kLDF[c]    = kL;
        mDotAds[c] = mDot;
        q[c]       = qOld + mDot*dt/((1.0 - epsV)*rhoSV);          // actual uptake
    }

    q.correctBoundaryConditions();
    qStar.correctBoundaryConditions();
    kLDF.correctBoundaryConditions();
    mDotAds.correctBoundaryConditions();
}
