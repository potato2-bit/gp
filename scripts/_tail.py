    ax.legend(l1+l2,la1+la2,loc='upper center')
    fig.savefig(os.path.join(FIG_DIR,'fig_monthly_water.pdf')); plt.close(fig)

    # Fig 3: COP & SEC vs dT
    fig,ax=plt.subplots()
    ax.plot(dT_range,cop_curve,'-',color='#1f77b4',label='COP')
    ax.set_xlabel(r'$\Delta T = T_H-T_C$ (K)'); ax.set_ylabel('COP (max)')
    ax2=ax.twinx(); ax2.plot(dT_range,sec_curve,'--',color='#d62728',label='SEC')
    ax2.set_ylabel('SEC (kWh/L, latent only)'); ax2.grid(False)
    l1,la1=ax.get_legend_handles_labels(); l2,la2=ax2.get_legend_handles_labels()
    ax.legend(l1+l2,la1+la2,loc='upper right')
    fig.savefig(os.path.join(FIG_DIR,'fig_cop_sec_dT.pdf')); plt.close(fig)

    # Fig 4: margin sensitivity
    fig,ax=plt.subplots()
    ax.plot(sens['margin'],sens['water_tile_Lyr'],'-o',ms=4,color='#1f77b4',
            label='Water/tile')
    ax.set_xlabel(r'Sub-cooling margin $\Delta T_{margin}$ (K)')
    ax.set_ylabel('Annual water/tile (L)')
    ax2=ax.twinx(); ax2.plot(sens['margin'],sens['sec_kWh_L'],'--s',ms=4,
                             color='#d62728',label='SEC')
    ax2.set_ylabel('SEC (kWh/L)'); ax2.grid(False)
    l1,la1=ax.get_legend_handles_labels(); l2,la2=ax2.get_legend_handles_labels()
    ax.legend(l1+l2,la1+la2,loc='upper left')
    fig.savefig(os.path.join(FIG_DIR,'fig_margin_sensitivity.pdf')); plt.close(fig)

    # Fig 5: energy balance - monthly TEC+aux energy vs dedicated PV supply
    fig,ax=plt.subplots()
    days=monthly['month'].map(lambda m: pd.Timestamp(2020,m,1).days_in_month)
    e_demand = monthly['energy_kWh_sys'] + (E_fans_day_Wh+E_mcu_day_Wh)*days/1000.0
    e_supply = P_pv_Wp/1000.0*PSH_BENBAN*PR_PV*days
    ax.bar(monthly['month']-0.18,e_demand,width=0.36,color='#d62728',
           alpha=0.8,label='Demand')
    ax.bar(monthly['month']+0.18,e_supply,width=0.36,color='#2ca02c',
           alpha=0.8,label='PV supply')
    ax.set_xlabel('Month'); ax.set_ylabel('Energy (kWh/month)')
    ax.set_xticks(range(1,13)); ax.set_xticklabels(MON); ax.legend()
    fig.savefig(os.path.join(FIG_DIR,'fig_energy_balance.pdf')); plt.close(fig)

    # Fig 6: diurnal profiles summer (Jul) vs winter (Jan)
    fig,ax=plt.subplots()
    for mth,c,lab in [(1,'#1f77b4','Jan'),(7,'#d62728','Jul')]:
        d=sim[sim['month']==mth].groupby('hour').agg(
            T=('T2M','mean'),Td=('Tdew','mean')).reset_index()
        ax.plot(d['hour'],d['T'],'-',color=c,label=f'{lab} $T_{{amb}}$')
        ax.plot(d['hour'],d['Td'],'--',color=c,label=f'{lab} $T_{{dew}}$')
    ax.axvspan(0,NIGHT_END,color='grey',alpha=0.12)
    ax.axvspan(NIGHT_START,23,color='grey',alpha=0.12)
    ax.set_xlabel('Hour of day'); ax.set_ylabel(r'Temperature ($^\circ$C)')
    ax.set_xlim(0,23); ax.legend(ncol=2,fontsize=7)
    fig.savefig(os.path.join(FIG_DIR,'fig_diurnal.pdf')); plt.close(fig)

    print("\n[Figures written] 6 PDFs in figures/")
    print("="*70)
    print(" DONE")
    print("="*70)
