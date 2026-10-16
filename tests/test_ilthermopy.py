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

    def test_compound_smiles_missing_not_nan(self):
        compounds = ilt.GetSavedCompounds()
        missing = compounds.data.loc[compounds.data.name == 'cholinium L-aspartate']
        assert len(missing) == 1
        assert missing.iloc[0].smiles == ''
        assert missing.iloc[0].id not in compounds.id2smiles
        assert 'cholinium L-aspartate' not in compounds.name2smiles

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
