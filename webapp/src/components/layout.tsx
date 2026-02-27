import { Link, Outlet, useLocation } from "react-router-dom";
import { FileText, HardDrive, LayoutDashboard, Settings, Terminal, Github, Server, History, Book, MessageSquare, Grid } from "lucide-react";
import { cn } from "@/shared/utils";

export default function Layout() {
    const location = useLocation();

    const navItems = [
        { href: "/", label: "Dashboard", icon: LayoutDashboard },
        { href: "/chat", label: "Chat", icon: MessageSquare },
        { href: "/apps", label: "Apps", icon: Grid },
        { href: "/files", label: "File Browser", icon: FileText },
        { href: "/tools", label: "Tools", icon: Terminal },
        { href: "/git", label: "Git Ops", icon: Github },
        { href: "/docker", label: "Docker", icon: Server },
        { href: "/logs", label: "Logs", icon: History },
        { href: "/settings", label: "Settings", icon: Settings },
        { href: "/help", label: "Help", icon: Book },
    ];

    return (
        <div className="flex h-screen bg-background text-foreground overflow-hidden font-sans antialiased">
            {/* Sidebar */}
            <aside className="w-64 border-r border-border bg-card/50 flex flex-col">
                <div className="p-6 border-b border-border">
                    <div className="flex items-center gap-2 font-bold text-xl tracking-tight">
                        <div className="p-2 bg-primary/10 rounded-lg text-primary">
                            <HardDrive className="w-6 h-6" />
                        </div>
                        <span>fs-mcp</span>
                    </div>
                    <div className="mt-2 text-xs text-muted-foreground font-mono">
                        v2.2.0 (SOTA)
                    </div>
                </div>

                <nav className="flex-1 p-4 space-y-1 overflow-y-auto">
                    {navItems.map((item) => {
                        const isActive = location.pathname === item.href;
                        return (
                            <Link
                                key={item.href}
                                to={item.href}
                                className={cn(
                                    "flex items-center gap-3 px-3 py-2.5 rounded-md transition-all duration-200 group",
                                    isActive
                                        ? "bg-primary text-primary-foreground font-medium shadow-sm"
                                        : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
                                )}
                            >
                                <item.icon className={cn("w-5 h-5", isActive ? "text-primary-foreground" : "text-muted-foreground group-hover:text-accent-foreground")} />
                                {item.label}
                            </Link>
                        );
                    })}
                </nav>

                <div className="p-4 border-t border-border bg-card/30">
                    <div className="flex items-center gap-3 px-3 py-2">
                        <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-indigo-500 to-purple-500 flex items-center justify-center text-white text-xs font-bold">
                            SS
                        </div>
                        <div className="flex flex-col">
                            <span className="text-sm font-medium">Sandra Schipal</span>
                            <span className="text-xs text-muted-foreground">Admin</span>
                        </div>
                    </div>
                </div>
            </aside>

            {/* Main Content */}
            <main className="flex-1 flex flex-col bg-background/95 backdrop-blur-sm relative overflow-hidden">
                {/* Top Bar can go here if needed */}
                <div className="flex-1 overflow-auto p-8 relative z-10 scroll-smooth">
                    <div className="max-w-7xl mx-auto space-y-8 animate-in fade-in duration-500 slide-in-from-bottom-4">
                        <Outlet />
                    </div>
                </div>

                {/* Background Gradients */}
                <div className="absolute top-0 left-0 w-full h-96 bg-gradient-to-b from-primary/5 to-transparent pointer-events-none -z-10" />
            </main>
        </div>
    );
}
