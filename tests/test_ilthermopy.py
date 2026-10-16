'''Unit tests for the ilthermopy package'''

import ilthermopy as ilt


class TestData:
    
    def test_properties(self):
        props = ilt.PropertyList()
        assert props
        assert props.prop2key['Activity']
    
    def test_entries(self):
        df = ilt.GetAllEntries()
        assert not df.empty  # do not pin live service size
        saved_ids = set(ilt.GetSavedCompounds().data.id)
        current_ids = set()
        for n in (1, 2, 3):
            current_ids.update(df[f'cmp{n}_id'].dropna())
        assert current_ids == saved_ids  # bundled snapshot covers current API
    
    def test_compounds(self):
        cmps = ilt.GetSavedCompounds().data
        assert len(cmps) == 3762  # pinned bundled data snapshot
        assert cmps.id.is_unique and cmps.name.is_unique


class TestSearch:
    
    def test_property_search(self):
        df = ilt.Search(n_compounds=3, prop='Activity', year=2010)
        assert len(df) > 0
    
    def test_retrieving_entry(self):
        df = ilt.Search(n_compounds=3, prop='Activity', year=2010)
        entries = [ilt.GetEntry(df['id'].iloc[0])]  # single API request
        assert entries[0].components[0]
        assert entries[0].components[0].smiles


class TestOfflineMaintenance:

    def test_api_endpoint_urls(self):
        import ilthermopy.requests as requests
        for url in (requests.PROPS_URL, requests.SEARCH_URL,
                    requests.DATA_URL, requests.IMAGE_URL):
            assert url.startswith('https://ilthermo.boulder.nist.gov/ILT2/')

    def test_cholinium_l_aspartate_structure(self):
        """Regression for the newly added structure annotation."""
        from ilthermopy.data_structs import ResponseToCompound

        expected = 'C(C(O)=O)[C@H](N)C([O-])=O.OCC[N+](C)(C)C'
        compounds = ilt.GetSavedCompounds()
        rows = compounds.data.loc[compounds.data.name == 'cholinium L-aspartate']
        assert len(rows) == 1
        row = rows.iloc[0]
        assert row.id == 'AAtWfr'
        assert row.smiles == expected
        assert compounds.id2smiles[row.id] == expected
        assert compounds.name2smiles[row['name']] == expected
        api_compound = ResponseToCompound(
            {'idout': row.id, 'name': row['name'], 'sample': []})
        assert api_compound.smiles == expected
        assert api_compound.smiles_error is None

    def test_all_saved_smiles_are_strings(self):
        compounds = ilt.GetSavedCompounds()
        assert all(isinstance(smi, str) and smi for smi in compounds.id2smiles.values())
        assert all(isinstance(smi, str) and smi for smi in compounds.name2smiles.values())

    def test_update_date_from_property_api(self, monkeypatch, capsys):
        import ilthermopy.updates as updates
        monkeypatch.setattr(
            updates._req, 'GetPropertyList',
            lambda: {'cprmsg': '<b> Updated on July      22, 2026.</b>'})
        updates.CheckLastUpdate()
        output = capsys.readouterr().out
        assert 'July 22, 2026' in output
        assert 'October 16, 2026' in output
        assert 'up-to-date' in output

    def test_update_date_bad_payload(self, monkeypatch):
        import pytest
        import ilthermopy.updates as updates
        from ilthermopy.errors import ILThermoResponseError
        monkeypatch.setattr(updates._req, 'GetPropertyList', lambda: {'plist': []})
        with pytest.raises(ILThermoResponseError):
            updates.CheckLastUpdate()


    def test_corrected_structural_annotations(self):
        """Guard known ID-reuse and nomenclature mistakes in the snapshot."""
        compounds = ilt.GetSavedCompounds()
        expected = [
            ("ABOMJk", "N-hexyl-N-methylmorpholinium N-acetyl-L-valinate", "CC(=O)N[C@H](C(=O)[O-])C(C)C.CCCCCC[N+]1(C)CCOCC1"),
            ("ABOMgM", "sodium hexadecyl sulfate", "CCCCCCCCCCCCCCCCOS(=O)(=O)[O-].[Na+]"),
            ("ABrsgp", "N-[(heptyloxy)methyl]-2-hydroxy-N,N-dimethylethanaminium 1,1,1-trifluoro-N-[(trifluoromethyl)sulfonyl]methanesulfonamide", "CCCCCCCOC[N+](C)(C)CCO.O=S(=O)([N-]S(=O)(=O)C(F)(F)F)C(F)(F)F"),
            ("AByVwu", "1-dodecyl-4-methyl-1H-1,2,4-triazol-4-ium bis((trifluoromethyl)sulfonyl)amide", "CCCCCCCCCCCCn1c[n+](C)cn1.O=S(=O)([N-]S(=O)(=O)C(F)(F)F)C(F)(F)F"),
            ("AByRdf", "4-benzyl-4-dodecmorpholinium (4-chlorophenoxy)acetate", "ClC1=CC=C(OCC(=O)[O-])C=C1.C(C1=CC=CC=C1)[N+]1(CCOCC1)CCCCCCCCCCCC"),
            ("ADRmZg", "1-decyl-3-methylimidazolium cobalt(II) hexafluoroacetylacetonate", "CCCCCCCCCC[n+]1ccn(C)c1.FC(F)(F)C1=[O+][Co-4]23(OC(C(F)(F)F)=CC(=[O+]2)C(F)(F)F)(OC(C(F)(F)F)=CC(=[O+]3)C(F)(F)F)OC(C(F)(F)F)=C1"),
            ("ADRkxz", "1-decyl-3-methylimidazolium nickel(II) hexafluoroacetylacetonate", "CCCCCCCCCC[n+]1ccn(C)c1.FC(F)(F)C1=[O+][Ni-4]23(OC(C(F)(F)F)=CC(=[O+]2)C(F)(F)F)(OC(C(F)(F)F)=CC(=[O+]3)C(F)(F)F)OC(C(F)(F)F)=C1"),
            ("ADSgVl", "1-decyl-3-methylimidazolium copper(II) hexafluoroacetylacetonate", "CCCCCCCCCC[n+]1ccn(C)c1.FC(F)(F)C1=[O+][Cu-4]23(OC(C(F)(F)F)=CC(=[O+]2)C(F)(F)F)(OC(C(F)(F)F)=CC(=[O+]3)C(F)(F)F)OC(C(F)(F)F)=C1"),
        ]
        for cid, name, smiles in expected:
            matching = compounds.data.loc[compounds.data['id'] == cid]
            assert len(matching) == 1
            assert matching.iloc[0]['name'] == name
            assert matching.iloc[0]['smiles'] == smiles
            assert compounds.id2smiles[cid] == smiles
            assert compounds.name2smiles[name] == smiles
