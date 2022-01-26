## Cambiare GTQ

Conector para tipo de cambio en ERPNext, basado en las tasas de cambio del Banco de Guatemala

> https://www.banguat.gob.gt/variables/ws/TipoCambio.asmx

#### License

GNU General Public License v3.0

### Installation instructions

**Supports ERPNext Version 13**

---

### How to Install

1. `bench get-app --branch production https://github.com/sihaysistema/cambiare-gtq.git`
2. `bench setup requirements`
3. `bench build --app cambiare_gtq`
4. `bench restart`
5. `bench --site [your.site.name] install-app cambiare_gtq`
6. `bench --site [your.site.name] migrate`

---

### How To Use:

[Cambiare GTQ Wiki](https://github.com/sihaysistema/cambiare_gtq/wiki)
