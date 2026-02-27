import { Activity, HardDrive, Cpu, GitBranch } from "lucide-react";

export default function Dashboard() {
    return (
        <div className="space-y-8">
            <div>
                <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
                <p className="text-muted-foreground mt-2">System overview and quick stats.</p>
            </div>

            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                {[
                    { title: "System Status", value: "Online", icon: Activity, color: "text-green-500" },
                    { title: "Disk Usage", value: "45%", icon: HardDrive, color: "text-blue-500" },
                    { title: "CPU Load", value: "12%", icon: Cpu, color: "text-purple-500" },
                    { title: "Active Repos", value: "7", icon: GitBranch, color: "text-orange-500" },
                ].map((stat, i) => (
                    <div key={i} className="rounded-xl border border-border bg-card p-6 shadow-sm transition-all hover:shadow-md hover:bg-card/80">
                        <div className="flex items-center justify-between space-y-0 pb-2">
                            <span className="text-sm font-medium text-muted-foreground">{stat.title}</span>
                            <stat.icon className={`h-4 w-4 ${stat.color}`} />
                        </div>
                        <div className="text-2xl font-bold">{stat.value}</div>
                    </div>
                ))}
            </div>

            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
                <div className="col-span-4 rounded-xl border border-border bg-card p-6">
                    <h3 className="font-semibold mb-4">Recent Activity</h3>
                    <div className="space-y-4">
                        {[1, 2, 3].map((_, i) => (
                            <div key={i} className="flex items-center gap-4">
                                <div className="h-2 w-2 rounded-full bg-primary" />
                                <div className="flex-1 space-y-1">
                                    <p className="text-sm font-medium leading-none">Modified server.py</p>
                                    <p className="text-xs text-muted-foreground">2 minutes ago</p>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
                <div className="col-span-3 rounded-xl border border-border bg-card p-6">
                    <h3 className="font-semibold mb-4">Quick Actions</h3>
                    <div className="space-y-2">
                        <button className="w-full rounded-md bg-accent px-4 py-2 text-sm font-medium hover:bg-accent/80 transition-colors text-left">
                            Run Tests
                        </button>
                        <button className="w-full rounded-md bg-accent px-4 py-2 text-sm font-medium hover:bg-accent/80 transition-colors text-left">
                            View Logs
                        </button>
                        <button className="w-full rounded-md bg-accent px-4 py-2 text-sm font-medium hover:bg-accent/80 transition-colors text-left">
                            New File
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}
