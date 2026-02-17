import { useState, useEffect } from 'react';
import { Save, RefreshCw } from 'lucide-react';

const API_URL = "http://localhost:8000";

export default function RGDUParameters() {
    const [params, setParams] = useState({
        heures_contractuelles: 151.67,
        effectif_50_et_plus: true,
        smic_mensuel: 1823.03,
        tdeltaopt: null
    });
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [message, setMessage] = useState(null);

    useEffect(() => {
        fetchParams();
    }, []);

    const fetchParams = async () => {
        setLoading(true);
        try {
            const res = await fetch(`${API_URL}/rgdu-params`);
            if (res.ok) {
                const data = await res.json();
                setParams(data);
            }
        } catch (err) {
            console.error("Failed to fetch params", err);
            setMessage({ type: 'error', text: "Erreur lors du chargement des paramètres." });
        } finally {
            setLoading(false);
        }
    };

    const handleSave = async (e) => {
        e.preventDefault();
        setSaving(true);
        setMessage(null);
        try {
            // Prepare payload, ensuring types are correct
            const payload = {
                ...params,
                heures_contractuelles: parseFloat(params.heures_contractuelles),
                smic_mensuel: parseFloat(params.smic_mensuel),
                tdeltaopt: params.tdeltaopt === "" ? null : (params.tdeltaopt ? parseFloat(params.tdeltaopt) : null)
            };

            const res = await fetch(`${API_URL}/rgdu-params`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload),
            });

            if (res.ok) {
                setMessage({ type: 'success', text: "Paramètres enregistrés avec succès." });
                const data = await res.json();
                setParams(data);
            } else {
                throw new Error("Failed to save");
            }
        } catch (err) {
            console.error("Failed to save", err);
            setMessage({ type: 'error', text: "Erreur lors de l'enregistrement." });
        } finally {
            setSaving(false);
        }
    };

    const handleChange = (e) => {
        const { name, value, type, checked } = e.target;
        setParams(prev => ({
            ...prev,
            [name]: type === 'checkbox' ? checked : value
        }));
    };

    return (
        <div style={{ padding: 24, paddingBottom: 100, overflowY: 'auto' }}>
            <div style={{ marginBottom: 24 }}>
                <h2>Paramètres RGDU</h2>
                <p style={{ color: '#64748b' }}>Configuration des variables pour le calcul de la réduction générale.</p>
            </div>

            {loading ? (
                <div>Chargement...</div>
            ) : (
                <form onSubmit={handleSave} style={{ maxWidth: 600 }}>

                    <div className="form-group" style={{ marginBottom: 16 }}>
                        <label style={{ display: 'block', marginBottom: 8, fontWeight: 500 }}>SMIC Mensuel (€)</label>
                        <input
                            type="number"
                            step="0.01"
                            name="smic_mensuel"
                            value={params.smic_mensuel}
                            onChange={handleChange}
                            style={{ width: '100%', padding: 8, borderRadius: 6, border: '1px solid #cbd5e1' }}
                        />
                    </div>

                    <div className="form-group" style={{ marginBottom: 16 }}>
                        <label style={{ display: 'block', marginBottom: 8, fontWeight: 500 }}>Heures Contractuelles</label>
                        <input
                            type="number"
                            step="0.01"
                            name="heures_contractuelles"
                            value={params.heures_contractuelles}
                            onChange={handleChange}
                            style={{ width: '100%', padding: 8, borderRadius: 6, border: '1px solid #cbd5e1' }}
                        />
                    </div>

                    <div className="form-group" style={{ marginBottom: 16 }}>
                        <label style={{ display: 'flex', alignItems: 'center', gap: 10, cursor: 'pointer' }}>
                            <input
                                type="checkbox"
                                name="effectif_50_et_plus"
                                checked={params.effectif_50_et_plus}
                                onChange={handleChange}
                                style={{ width: 18, height: 18 }}
                            />
                            <span style={{ fontWeight: 500 }}>Effectif ≥ 50 salariés</span>
                        </label>
                        <p style={{ fontSize: '0.85em', color: '#64748b', marginLeft: 28, marginTop: 4 }}>
                            Impacte le calcul du Tdelta (FNAL).
                        </p>
                    </div>

                    <div className="form-group" style={{ marginBottom: 24 }}>
                        <label style={{ display: 'block', marginBottom: 8, fontWeight: 500 }}>Tdelta Optionnel (Override)</label>
                        <input
                            type="number"
                            step="0.0001"
                            name="tdeltaopt"
                            value={params.tdeltaopt || ""}
                            placeholder="Laisser vide pour utiliser la valeur standard"
                            onChange={handleChange}
                            style={{ width: '100%', padding: 8, borderRadius: 6, border: '1px solid #cbd5e1' }}
                        />
                        <p style={{ fontSize: '0.85em', color: '#64748b', marginTop: 4 }}>
                            Si renseigné, remplace la valeur Tdelta standard.
                        </p>
                    </div>

                    {message && (
                        <div style={{
                            marginBottom: 16,
                            padding: 12,
                            borderRadius: 6,
                            background: message.type === 'error' ? '#fee2e2' : '#dcfce7',
                            color: message.type === 'error' ? '#b91c1c' : '#15803d'
                        }}>
                            {message.text}
                        </div>
                    )}

                    <div style={{ display: 'flex', gap: 12 }}>
                        <button
                            type="submit"
                            disabled={saving}
                            style={{
                                display: 'flex', alignItems: 'center', gap: 8,
                                background: '#2563eb', color: 'white', border: 'none', padding: '10px 20px', borderRadius: 6, cursor: 'pointer', fontWeight: 500
                            }}
                        >
                            {saving ? "Enregistrement..." : <><Save size={18} /> Enregistrer</>}
                        </button>
                        <button
                            type="button"
                            onClick={fetchParams}
                            style={{
                                display: 'flex', alignItems: 'center', gap: 8,
                                background: '#f1f5f9', color: '#475569', border: '1px solid #cbd5e1', padding: '10px 20px', borderRadius: 6, cursor: 'pointer', fontWeight: 500
                            }}
                        >
                            <RefreshCw size={18} /> Annuler
                        </button>
                    </div>
                </form>
            )}
        </div>
    );
}
