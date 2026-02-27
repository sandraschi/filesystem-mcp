import { useState, useEffect } from "react";
import { useTheme } from "@/components/theme-provider";
import { Monitor, Moon, Sun, Save, Server, Key, Cpu, RefreshCw, AlertCircle } from "lucide-react";

type LlmProvider = 'ollama' | 'lm-studio' | 'openai' | 'anthropic' | 'gemini';

interface LlmConfig {
    provider: LlmProvider;
    baseUrl: string;
    apiKey: string;
    model: string;
}

const DEFAULT_CONFIG: LlmConfig = {
    provider: 'ollama',
    baseUrl: 'http://localhost:11434',
    apiKey: '',
    model: 'llama3'
};

export default function Settings() {
    const { setTheme, theme } = useTheme();
    const [config, setConfig] = useState<LlmConfig>(DEFAULT_CONFIG);
    const [status, setStatus] = useState<string>("");
    const [availableModels, setAvailableModels] = useState<string[]>([]);
    const [isLoadingModels, setIsLoadingModels] = useState(false);
    const [modelError, setModelError] = useState("");

    useEffect(() => {
        const saved = localStorage.getItem("llm_config");
        if (saved) {
            try {
                const parsed = JSON.parse(saved);
                setConfig({ ...DEFAULT_CONFIG, ...parsed });
                // Attempt to fetch models if we have a base url
                if (parsed.baseUrl && (parsed.provider === 'ollama' || parsed.provider === 'lm-studio')) {
                    fetchModels(parsed.provider, parsed.baseUrl);
                }
            } catch (e) {
                console.error("Failed to parse saved config", e);
            }
        }
    }, []);

    const handleSave = () => {
        localStorage.setItem("llm_config", JSON.stringify(config));
        setStatus("Settings saved successfully!");
        setTimeout(() => setStatus(""), 3000);
    };

    const updateConfig = (key: keyof LlmConfig, value: string) => {
        setConfig(prev => {
            const newConfig = { ...prev, [key]: value };
            if (key === 'provider') {
                handleProviderChange(value as LlmProvider);
                return prev; // handleProviderChange sets the state
            }
            return newConfig;
        });
    };

    const handleProviderChange = (provider: LlmProvider) => {
        let newBaseUrl = config.baseUrl;
        if (provider === 'ollama') newBaseUrl = 'http://localhost:11434';
        if (provider === 'lm-studio') newBaseUrl = 'http://localhost:1234/v1';
        if (provider === 'openai') newBaseUrl = 'https://api.openai.com/v1';
        if (provider === 'anthropic') newBaseUrl = 'https://api.anthropic.com/v1';
        if (provider === 'gemini') newBaseUrl = 'https://generativelanguage.googleapis.com/v1beta';

        setConfig(prev => ({ ...prev, provider, baseUrl: newBaseUrl, model: '' }));
        setAvailableModels([]);
        setModelError("");

        if (provider === 'ollama' || provider === 'lm-studio') {
            fetchModels(provider, newBaseUrl);
        }
    };

    const fetchModels = async (provider: LlmProvider, baseUrl: string) => {
        setIsLoadingModels(true);
        setModelError("");
        try {
            let url = "";
            let transform = (data: any) => [];

            if (provider === 'ollama') {
                url = `${baseUrl.replace(/\/$/, '')}/api/tags`;
                transform = (data) => data.models?.map((m: any) => m.name) || [];
            } else if (provider === 'lm-studio') {
                url = `${baseUrl.replace(/\/$/, '')}/models`;
                transform = (data) => data.data?.map((m: any) => m.id) || [];
            } else {
                return; // Cloud providers might need authentications proxy, skipping for now
            }

            const res = await fetch(url);
            if (!res.ok) throw new Error(`Failed to fetch models: ${res.statusText}`);
            const data = await res.json();
            const models = transform(data);
            setAvailableModels(models);

            if (models.length > 0 && !config.model) {
                setConfig(prev => ({ ...prev, model: models[0] }));
            }
        } catch (e: any) {
            console.error("Error fetching models:", e);
            setModelError("Could not load models. Ensure provider is running.");
        } finally {
            setIsLoadingModels(false);
        }
    };

    return (
        <div className="space-y-8 max-w-4xl mx-auto pb-20">
            <div>
                <h1 className="text-3xl font-bold tracking-tight">Settings</h1>
                <p className="text-muted-foreground mt-2">Manage application preferences and LLM configuration.</p>
            </div>

            <div className="space-y-6">
                {/* Appearance */}
                <section className="rounded-xl border border-border bg-card p-6 space-y-4">
                    <h2 className="text-xl font-semibold flex items-center gap-2">
                        <Monitor className="w-5 h-5" /> Appearance
                    </h2>
                    <div className="flex flex-col sm:flex-row gap-4">
                        <button
                            onClick={() => setTheme("light")}
                            className={`flex items-center gap-2 px-4 py-2 rounded-md border transition-all ${theme === "light"
                                ? "border-primary bg-primary/10 text-primary"
                                : "border-border hover:bg-accent"
                                }`}
                        >
                            <Sun className="w-4 h-4" /> Light
                        </button>
                        <button
                            onClick={() => setTheme("dark")}
                            className={`flex items-center gap-2 px-4 py-2 rounded-md border transition-all ${theme === "dark"
                                ? "border-primary bg-primary/10 text-primary"
                                : "border-border hover:bg-accent"
                                }`}
                        >
                            <Moon className="w-4 h-4" /> Dark
                        </button>
                        <button
                            onClick={() => setTheme("system")}
                            className={`flex items-center gap-2 px-4 py-2 rounded-md border transition-all ${theme === "system"
                                ? "border-primary bg-primary/10 text-primary"
                                : "border-border hover:bg-accent"
                                }`}
                        >
                            <Monitor className="w-4 h-4" /> System
                        </button>
                    </div>
                </section>

                {/* LLM Configuration */}
                <section className="rounded-xl border border-border bg-card p-6 space-y-4">
                    <h2 className="text-xl font-semibold flex items-center gap-2">
                        <Cpu className="w-5 h-5" /> Local LLM Configuration
                    </h2>
                    <div className="grid gap-4">
                        <div className="space-y-2">
                            <label className="text-sm font-medium">Provider</label>
                            <select
                                value={config.provider}
                                onChange={(e) => handleProviderChange(e.target.value as LlmProvider)}
                                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                            >
                                <option value="ollama">Ollama (Local)</option>
                                <option value="lm-studio">LM Studio (Local)</option>
                                <option value="openai">OpenAI (Cloud)</option>
                                <option value="anthropic">Anthropic (Cloud)</option>
                                <option value="gemini">Google Gemini (Cloud)</option>
                            </select>
                        </div>

                        <div className="space-y-2">
                            <label className="text-sm font-medium flex items-center gap-2">
                                <Server className="w-4 h-4" /> Base URL
                            </label>
                            <input
                                value={config.baseUrl}
                                onChange={(e) => updateConfig('baseUrl', e.target.value)}
                                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                                placeholder="http://localhost:11434"
                            />
                        </div>

                        <div className="space-y-2">
                            <label className="text-sm font-medium flex items-center gap-2">
                                <Key className="w-4 h-4" /> API Key
                            </label>
                            <input
                                type="password"
                                value={config.apiKey}
                                onChange={(e) => updateConfig('apiKey', e.target.value)}
                                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                                placeholder={config.provider === 'ollama' ? "Not required for Ollama" : "sk-..."}
                                disabled={config.provider === 'ollama'}
                            />
                        </div>

                        <div className="space-y-2">
                            <label className="text-sm font-medium flex items-center justify-between">
                                <span>Model Name</span>
                                {(config.provider === 'ollama' || config.provider === 'lm-studio') && (
                                    <button
                                        onClick={() => fetchModels(config.provider, config.baseUrl)}
                                        className="text-xs text-primary flex items-center gap-1 hover:underline"
                                        disabled={isLoadingModels}
                                    >
                                        <RefreshCw className={`w-3 h-3 ${isLoadingModels ? 'animate-spin' : ''}`} />
                                        Refresh Models
                                    </button>
                                )}
                            </label>

                            {availableModels.length > 0 ? (
                                <select
                                    value={config.model}
                                    onChange={(e) => updateConfig('model', e.target.value)}
                                    className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                                >
                                    <option value="" disabled>Select a model</option>
                                    {availableModels.map(m => (
                                        <option key={m} value={m}>{m}</option>
                                    ))}
                                </select>
                            ) : (
                                <input
                                    value={config.model}
                                    onChange={(e) => updateConfig('model', e.target.value)}
                                    className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                                    placeholder="e.g. llama3, gpt-4o, claude-3-opus"
                                />
                            )}

                            {modelError && (
                                <p className="text-xs text-red-500 flex items-center gap-1">
                                    <AlertCircle className="w-3 h-3" /> {modelError}
                                </p>
                            )}
                            <p className="text-xs text-muted-foreground">
                                Verify this model is downloaded in your local provider.
                            </p>
                        </div>
                    </div>
                </section>

                <div className="flex justify-between items-center pt-4">
                    <span className="text-green-500 text-sm font-medium">{status}</span>
                    <button
                        onClick={handleSave}
                        className="flex items-center gap-2 bg-primary text-primary-foreground hover:bg-primary/90 px-4 py-2 rounded-md font-medium transition-colors"
                    >
                        <Save className="w-4 h-4" /> Save Configuration
                    </button>
                </div>
            </div>
        </div>
    );
}
