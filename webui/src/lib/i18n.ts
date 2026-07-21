import i18n from "i18next";
import { initReactI18next } from "react-i18next";

const resources = {
  en: {
    translation: {
      brand: "KToolBox",
      subtitle: "Pawchive sync workspace",
      login: {
        title: "Sign in to this project",
        description: "Use the account configured by the project owner.",
        username: "Username",
        password: "Password",
        submit: "Sign in",
        signingIn: "Signing in",
        failed: "Sign-in failed",
      },
      nav: {
        overview: "Overview",
        tasks: "Tasks",
        creators: "Creators",
        posts: "Posts",
        blockers: "Blockers",
        configuration: "Configuration",
        system: "System",
      },
      shell: {
        menu: "Open navigation",
        closeMenu: "Close navigation",
        light: "Use light theme",
        dark: "Use dark theme",
        language: "Switch language",
        logout: "Sign out",
        securityTitle: "Trusted networks only",
        securityBody: "This session uses HTTP. Credentials and task data are not encrypted in transit.",
      },
      overview: {
        eyebrow: "Project workspace",
        title: "Download operations at a glance",
        description: "Monitor queued work, keep creator rules current, and launch the next sync.",
        active: "Active tasks",
        queued: "Waiting",
        completed: "Completed",
        creators: "Enabled creators",
        recent: "Recent tasks",
        empty: "No tasks yet",
        openTasks: "Open task queue",
        newSync: "Create sync task",
        projectPath: "Project directory",
      },
      system: {
        title: "System",
        description: "Project paths, application versions, and runtime status.",
        appVersion: "KToolBox version",
        pawchiveVersion: "Pawchive version",
        projectConfig: "Project configuration",
        environmentFiles: "Environment files",
        check: "Check Pawchive",
        unavailable: "Unavailable",
      },
      common: {
        loading: "Loading",
        retry: "Retry",
        status: "Status",
        type: "Type",
        created: "Created",
        actions: "Actions",
        sync: "Sync",
        download: "Download",
        unknown: "Unknown",
      },
    },
  },
  "zh-CN": {
    translation: {
      brand: "KToolBox",
      subtitle: "Pawchive 同步工作台",
      login: {
        title: "登录此同步项目",
        description: "请使用项目所有者配置的账户。",
        username: "用户名",
        password: "密码",
        submit: "登录",
        signingIn: "正在登录",
        failed: "登录失败",
      },
      nav: {
        overview: "概览",
        tasks: "任务",
        creators: "作者",
        posts: "投稿",
        blockers: "屏蔽器",
        configuration: "配置",
        system: "系统",
      },
      shell: {
        menu: "打开导航",
        closeMenu: "关闭导航",
        light: "切换浅色模式",
        dark: "切换深色模式",
        language: "切换语言",
        logout: "退出登录",
        securityTitle: "仅在可信网络中使用",
        securityBody: "当前会话使用 HTTP，凭据和任务数据在传输过程中不会加密。",
      },
      overview: {
        eyebrow: "项目工作台",
        title: "一览下载运行状态",
        description: "查看队列、维护作者规则，并快速开始下一次同步。",
        active: "活动任务",
        queued: "等待中",
        completed: "已完成",
        creators: "启用作者",
        recent: "最近任务",
        empty: "还没有任务",
        openTasks: "打开任务队列",
        newSync: "创建同步任务",
        projectPath: "项目目录",
      },
      system: {
        title: "系统",
        description: "查看项目路径、应用版本与运行状态。",
        appVersion: "KToolBox 版本",
        pawchiveVersion: "Pawchive 版本",
        projectConfig: "项目配置",
        environmentFiles: "环境配置文件",
        check: "检查 Pawchive",
        unavailable: "不可用",
      },
      common: {
        loading: "加载中",
        retry: "重试",
        status: "状态",
        type: "类型",
        created: "创建时间",
        actions: "操作",
        sync: "同步",
        download: "下载",
        unknown: "未知",
      },
    },
  },
} as const;

const storedLanguage = localStorage.getItem("ktoolbox-language");
const browserLanguage = navigator.language.toLowerCase().startsWith("zh") ? "zh-CN" : "en";

void i18n.use(initReactI18next).init({
  resources,
  lng: storedLanguage || browserLanguage,
  fallbackLng: "en",
  interpolation: { escapeValue: false },
});

export async function toggleLanguage(): Promise<void> {
  const next = i18n.resolvedLanguage === "zh-CN" ? "en" : "zh-CN";
  localStorage.setItem("ktoolbox-language", next);
  await i18n.changeLanguage(next);
}

export default i18n;
