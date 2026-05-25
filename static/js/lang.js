// ════════════════════════════════════════════════════════════
// StackSage v2.0 — Language Switcher
// English / 中文 / বাংলা
// ════════════════════════════════════════════════════════════

const translations = {
  en: {
    nav_explore: 'Explore', nav_history: 'History',
    nav_bookmarks: 'Bookmarks', nav_compare: 'Compare',
    nav_about: 'About', nav_feedback: 'Feedback',

    hero_badge: 'AI-Powered Analysis',
    hero_title1: 'Discover What',
    hero_title2: 'Developers Build',
    hero_sub: 'Search any technology domain. Get real GitHub data, AI-generated trend insights, interactive charts, and a personalized learning roadmap — instantly.',
    search_placeholder: 'e.g. machine learning, web3, rust game engine…',
    search_btn: 'Analyze',
    try_label: 'Try:',

    feat1_title: 'Live GitHub Data',
    feat1_desc: 'Pulls real-time repository data — stars, forks, languages, topics, and commit activity.',
    feat2_title: 'AI Insights',
    feat2_desc: 'Advanced prompt engineering extracts trends, rising stars, gaps, and future predictions.',
    feat3_title: '5 Visual Charts',
    feat3_desc: 'Stars ranking, language distribution, activity scatter, topic word cloud, and timeline.',
    feat4_title: 'Learning Roadmap',
    feat4_desc: 'AI generates a custom 3-phase learning path based on the actual tools used by top projects.',
    feat5_title: 'AI Chat',
    feat5_desc: 'Ask follow-up questions about your results and get instant, contextual answers.',
    feat6_title: 'PDF + Share',
    feat6_desc: 'Export analysis as a clean PDF report or share a public link with your team.',

    recent_title: 'Recent Searches',
    new_search: 'New Search', export_pdf: 'Export PDF', share_link: 'Share',
    chat_open: 'Chat with AI', chat_send: 'Send',
    chat_placeholder: 'Ask anything about these results…',

    compare_title: 'Compare Two Domains',
    compare_sub: 'Side-by-side data + AI verdict on which is better for what.',
    compare_a: 'Domain A', compare_b: 'Domain B',
    compare_btn: 'Compare Now',

    auth_login: 'Sign In', auth_signup: 'Sign Up', auth_logout: 'Logout',
    auth_profile: 'Profile', auth_settings: 'Settings',

    bookmark_empty: 'No bookmarks yet.',
    history_empty: 'No search history yet.',
    history_title: 'Search History',
    bookmark_title: 'My Bookmarks',

    student_title: 'Student Zone',
    student_sub: 'Resources, roadmaps, and tools for students.',
    todo_title: 'Daily To-Do',
    todo_placeholder: 'Add a task…',
    todo_add: 'Add',

    about_what: 'What is this?',
    about_why: 'Why use it?',
    about_how: 'How to use it?',
    about_supported: "What's supported?",

    word_of_day: 'Word of the Day',
    footer_dev: 'Built with ❤️',
    loading: 'Analyzing…',
    error_msg: 'Something went wrong. Please try again.',
  },

  zh: {
    nav_explore: '探索', nav_history: '历史',
    nav_bookmarks: '书签', nav_compare: '比较',
    nav_about: '关于', nav_feedback: '反馈',

    hero_badge: 'AI 驱动分析',
    hero_title1: '发现开发者',
    hero_title2: '正在构建什么',
    hero_sub: '搜索任何技术领域，获取真实的 GitHub 数据、AI 生成的趋势洞察、交互式图表和个性化学习路线图。',
    search_placeholder: '例如：机器学习、区块链、游戏引擎…',
    search_btn: '分析',
    try_label: '试试：',

    feat1_title: '实时 GitHub 数据',
    feat1_desc: '获取实时仓库数据 — 星标、分叉、语言、话题和提交活动。',
    feat2_title: 'AI 洞察',
    feat2_desc: '先进的提示工程提取趋势、新兴项目、差距和未来预测。',
    feat3_title: '5 种可视化图表',
    feat3_desc: '星标排名、语言分布、活动散点图、话题词云和时间线。',
    feat4_title: '学习路线图',
    feat4_desc: 'AI 根据顶级项目实际使用的工具生成定制化三阶段学习路径。',
    feat5_title: 'AI 聊天',
    feat5_desc: '就您的结果提出后续问题，获得即时上下文答案。',
    feat6_title: 'PDF + 分享',
    feat6_desc: '将分析导出为整洁的 PDF 报告或与您的团队共享公共链接。',

    recent_title: '最近搜索',
    new_search: '新搜索', export_pdf: '导出 PDF', share_link: '分享',
    chat_open: '与 AI 聊天', chat_send: '发送',
    chat_placeholder: '关于这些结果问我什么…',

    compare_title: '比较两个领域',
    compare_sub: '并排数据 + AI 判定哪个更适合什么。',
    compare_a: '领域 A', compare_b: '领域 B',
    compare_btn: '立即比较',

    auth_login: '登录', auth_signup: '注册', auth_logout: '退出',
    auth_profile: '个人资料', auth_settings: '设置',

    bookmark_empty: '还没有书签。',
    history_empty: '还没有搜索历史。',
    history_title: '搜索历史',
    bookmark_title: '我的书签',

    student_title: '学生专区',
    student_sub: '为学生提供的资源、路线图和工具。',
    todo_title: '每日待办',
    todo_placeholder: '添加任务…',
    todo_add: '添加',

    about_what: '这是什么？',
    about_why: '为什么使用它？',
    about_how: '如何使用？',
    about_supported: '支持什么？',

    word_of_day: '每日词汇',
    footer_dev: '用心打造 ❤️',
    loading: '分析中…',
    error_msg: '出了点问题，请重试。',
  },

  bn: {
    nav_explore: 'অন্বেষণ', nav_history: 'ইতিহাস',
    nav_bookmarks: 'বুকমার্ক', nav_compare: 'তুলনা',
    nav_about: 'সম্পর্কে', nav_feedback: 'মতামত',

    hero_badge: 'AI চালিত বিশ্লেষণ',
    hero_title1: 'আবিষ্কার করুন',
    hero_title2: 'ডেভেলপাররা কী বানাচ্ছে',
    hero_sub: 'যেকোনো প্রযুক্তি ডোমেইন সার্চ করুন। আসল GitHub ডেটা, AI-জেনারেটেড ট্রেন্ড বিশ্লেষণ, ইন্টারেক্টিভ চার্ট এবং ব্যক্তিগতকৃত লার্নিং রোডম্যাপ পান — তাৎক্ষণিকভাবে।',
    search_placeholder: 'যেমন: মেশিন লার্নিং, ব্লকচেইন, গেম ইঞ্জিন…',
    search_btn: 'বিশ্লেষণ করুন',
    try_label: 'চেষ্টা করুন:',

    feat1_title: 'লাইভ GitHub ডেটা',
    feat1_desc: 'রিয়েল-টাইম রিপোজিটরি ডেটা — স্টার, ফর্ক, ভাষা, টপিক এবং কমিট অ্যাক্টিভিটি।',
    feat2_title: 'AI বিশ্লেষণ',
    feat2_desc: 'উন্নত প্রম্পট ইঞ্জিনিয়ারিং ট্রেন্ড, উদীয়মান প্রজেক্ট এবং ভবিষ্যৎ পূর্বাভাস বের করে।',
    feat3_title: '৫টি ভিজুয়াল চার্ট',
    feat3_desc: 'স্টার র‍্যাংকিং, ভাষা বিতরণ, অ্যাক্টিভিটি স্ক্যাটার, টপিক ওয়ার্ড ক্লাউড এবং টাইমলাইন।',
    feat4_title: 'লার্নিং রোডম্যাপ',
    feat4_desc: 'AI শীর্ষ প্রজেক্টে ব্যবহৃত আসল টুলের উপর ভিত্তি করে কাস্টম ৩-ধাপের শেখার পথ তৈরি করে।',
    feat5_title: 'AI চ্যাট',
    feat5_desc: 'আপনার ফলাফল সম্পর্কে ফলো-আপ প্রশ্ন জিজ্ঞাসা করুন এবং তাৎক্ষণিক, প্রাসঙ্গিক উত্তর পান।',
    feat6_title: 'PDF + শেয়ার',
    feat6_desc: 'বিশ্লেষণ পরিষ্কার PDF রিপোর্ট হিসেবে এক্সপোর্ট করুন বা আপনার দলের সাথে পাবলিক লিংক শেয়ার করুন।',

    recent_title: 'সাম্প্রতিক অনুসন্ধান',
    new_search: 'নতুন অনুসন্ধান', export_pdf: 'PDF এক্সপোর্ট', share_link: 'শেয়ার',
    chat_open: 'AI এর সাথে চ্যাট', chat_send: 'পাঠান',
    chat_placeholder: 'এই ফলাফল সম্পর্কে কিছু জিজ্ঞাসা করুন…',

    compare_title: 'দুটি ডোমেইন তুলনা করুন',
    compare_sub: 'পাশাপাশি ডেটা + কোনটি কিসের জন্য ভালো সেই AI রায়।',
    compare_a: 'ডোমেইন A', compare_b: 'ডোমেইন B',
    compare_btn: 'এখন তুলনা করুন',

    auth_login: 'সাইন ইন', auth_signup: 'সাইন আপ', auth_logout: 'লগআউট',
    auth_profile: 'প্রোফাইল', auth_settings: 'সেটিংস',

    bookmark_empty: 'এখনো কোনো বুকমার্ক নেই।',
    history_empty: 'এখনো কোনো সার্চ ইতিহাস নেই।',
    history_title: 'সার্চ ইতিহাস',
    bookmark_title: 'আমার বুকমার্ক',

    student_title: 'শিক্ষার্থী অঞ্চল',
    student_sub: 'শিক্ষার্থীদের জন্য রিসোর্স, রোডম্যাপ এবং টুলস।',
    todo_title: 'দৈনিক কাজের তালিকা',
    todo_placeholder: 'একটি কাজ যোগ করুন…',
    todo_add: 'যোগ করুন',

    about_what: 'এটা কী?',
    about_why: 'কেন ব্যবহার করবেন?',
    about_how: 'কীভাবে ব্যবহার করবেন?',
    about_supported: 'কী সমর্থিত?',

    word_of_day: 'আজকের শব্দ',
    footer_dev: 'ভালোবাসা দিয়ে তৈরি ❤️',
    loading: 'বিশ্লেষণ করা হচ্ছে…',
    error_msg: 'কিছু একটা ভুল হয়েছে। আবার চেষ্টা করুন।',
  }
};

function applyLanguage(lang) {
  const t = translations[lang];
  if (!t) return;
  localStorage.setItem('stacksage_lang', lang);

  document.querySelectorAll('[data-i18n]').forEach(el => {
    const key = el.getAttribute('data-i18n');
    if (t[key]) {
      if (el.tagName === 'INPUT' && el.hasAttribute('placeholder')) {
        el.placeholder = t[key];
      } else {
        el.textContent = t[key];
      }
    }
  });

  document.querySelectorAll('.lang-btn').forEach(btn => {
    btn.classList.toggle('lang-active', btn.getAttribute('data-lang') === lang);
  });

  // Update page direction for Chinese
  document.documentElement.lang = lang === 'zh' ? 'zh-CN' : lang === 'bn' ? 'bn' : 'en';
}

document.addEventListener('DOMContentLoaded', () => {
  const saved = localStorage.getItem('stacksage_lang') || 'en';
  applyLanguage(saved);
});
