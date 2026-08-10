import type { TranslationShape } from "./types";

const en = {
  label: "NSFW mode",
  enabled: "NSFW mode is on",
  disabled: "NSFW mode is off",
  description: "Show creator and work media that may contain explicit content.",
  change: "Change NSFW media mode",
  confirmTitle: "Enable NSFW media previews?",
  confirmBody: "Creator avatars, banners, work covers, attachments, and content images may contain explicit material.",
  confirmPersistence: "This choice stays enabled in this browser until you turn it off.",
  confirmNetwork: "KToolBox will request media through its authenticated same-origin proxy.",
  confirmAction: "Enable NSFW mode",
  unavailable: "Preview unavailable",
  tooLarge: "This image is too large to preview.",
  unsupported: "This file is not a supported preview image.",
  retry: "Retry preview",
  gallery: "Media gallery",
  cover: "Cover",
  loadMore: "Show 12 more",
  viewer: "Media viewer",
  previous: "Previous image",
  next: "Next image",
  imagePosition: "Image {{current}} of {{total}}",
  coverAlt: "Cover for {{title}}",
  avatarAlt: "Avatar for {{name}}",
  bannerAlt: "Banner for {{name}}",
  mediaAlt: "Media preview {{index}}",
  safeTitle: "Media previews are off",
  safeBody: "Enable NSFW mode to load remote image previews. Text and task controls remain available.",
} as const;

export const sensitiveMediaTranslations = {
  en,
  "zh-CN": {
    label: "NSFW 模式", enabled: "NSFW 模式已开启", disabled: "NSFW 模式已关闭", description: "显示可能包含成人内容的作者和作品媒体。", change: "调整 NSFW 媒体模式", confirmTitle: "开启 NSFW 媒体预览？", confirmBody: "作者头像、横幅、作品封面、附件和正文图片可能包含成人内容。", confirmPersistence: "此选择会保存在当前浏览器中，直到你主动关闭。", confirmNetwork: "KToolBox 将通过经过身份验证的同源代理请求媒体。", confirmAction: "开启 NSFW 模式", unavailable: "无法显示预览", tooLarge: "图片过大，无法预览。", unsupported: "该文件不是受支持的预览图片。", retry: "重试预览", gallery: "媒体画廊", cover: "封面", loadMore: "再显示 12 张", viewer: "媒体查看器", previous: "上一张图片", next: "下一张图片", imagePosition: "第 {{current}} / {{total}} 张", coverAlt: "{{title}}的封面", avatarAlt: "{{name}}的头像", bannerAlt: "{{name}}的横幅", mediaAlt: "媒体预览 {{index}}", safeTitle: "媒体预览已关闭", safeBody: "开启 NSFW 模式后才会加载远程图片；文本和任务操作仍可正常使用。",
  },
  "zh-Hant": {
    label: "NSFW 模式", enabled: "NSFW 模式已開啟", disabled: "NSFW 模式已關閉", description: "顯示可能包含成人內容的作者與作品媒體。", change: "調整 NSFW 媒體模式", confirmTitle: "開啟 NSFW 媒體預覽？", confirmBody: "作者頭像、橫幅、作品封面、附件和正文圖片可能包含成人內容。", confirmPersistence: "此選擇會保存在目前瀏覽器中，直到你主動關閉。", confirmNetwork: "KToolBox 將透過已驗證身分的同源代理請求媒體。", confirmAction: "開啟 NSFW 模式", unavailable: "無法顯示預覽", tooLarge: "圖片過大，無法預覽。", unsupported: "此檔案不是支援的預覽圖片。", retry: "重試預覽", gallery: "媒體畫廊", cover: "封面", loadMore: "再顯示 12 張", viewer: "媒體檢視器", previous: "上一張圖片", next: "下一張圖片", imagePosition: "第 {{current}} / {{total}} 張", coverAlt: "{{title}}的封面", avatarAlt: "{{name}}的頭像", bannerAlt: "{{name}}的橫幅", mediaAlt: "媒體預覽 {{index}}", safeTitle: "媒體預覽已關閉", safeBody: "開啟 NSFW 模式後才會載入遠端圖片；文字與工作操作仍可正常使用。",
  },
  ja: {
    label: "NSFW モード", enabled: "NSFW モードはオンです", disabled: "NSFW モードはオフです", description: "成人向けコンテンツを含む可能性があるクリエイターと作品のメディアを表示します。", change: "NSFW メディアモードを変更", confirmTitle: "NSFW メディアプレビューを有効にしますか？", confirmBody: "クリエイターのアバター、バナー、作品カバー、添付画像、本文画像には成人向けコンテンツが含まれる場合があります。", confirmPersistence: "この設定はオフにするまで現在のブラウザーに保存されます。", confirmNetwork: "KToolBox は認証済みの同一オリジンプロキシ経由でメディアを取得します。", confirmAction: "NSFW モードを有効化", unavailable: "プレビューを表示できません", tooLarge: "画像が大きすぎるためプレビューできません。", unsupported: "このファイルはプレビュー対応画像ではありません。", retry: "プレビューを再試行", gallery: "メディアギャラリー", cover: "カバー", loadMore: "さらに12枚表示", viewer: "メディアビューアー", previous: "前の画像", next: "次の画像", imagePosition: "{{total}} 枚中 {{current}} 枚目", coverAlt: "{{title}}のカバー", avatarAlt: "{{name}}のアバター", bannerAlt: "{{name}}のバナー", mediaAlt: "メディアプレビュー {{index}}", safeTitle: "メディアプレビューはオフです", safeBody: "NSFW モードを有効にするとリモート画像を読み込みます。テキストとタスク操作は引き続き利用できます。",
  },
  ko: {
    label: "NSFW 모드", enabled: "NSFW 모드 켜짐", disabled: "NSFW 모드 꺼짐", description: "성인 콘텐츠가 포함될 수 있는 크리에이터 및 작품 미디어를 표시합니다.", change: "NSFW 미디어 모드 변경", confirmTitle: "NSFW 미디어 미리보기를 켤까요?", confirmBody: "크리에이터 아바타, 배너, 작품 표지, 첨부 이미지 및 본문 이미지에 성인 콘텐츠가 포함될 수 있습니다.", confirmPersistence: "이 설정은 끌 때까지 현재 브라우저에 저장됩니다.", confirmNetwork: "KToolBox는 인증된 동일 출처 프록시를 통해 미디어를 요청합니다.", confirmAction: "NSFW 모드 켜기", unavailable: "미리보기를 표시할 수 없음", tooLarge: "이미지가 너무 커서 미리볼 수 없습니다.", unsupported: "이 파일은 지원되는 미리보기 이미지가 아닙니다.", retry: "미리보기 다시 시도", gallery: "미디어 갤러리", cover: "표지", loadMore: "12개 더 보기", viewer: "미디어 뷰어", previous: "이전 이미지", next: "다음 이미지", imagePosition: "{{total}}개 중 {{current}}번째", coverAlt: "{{title}} 표지", avatarAlt: "{{name}} 아바타", bannerAlt: "{{name}} 배너", mediaAlt: "미디어 미리보기 {{index}}", safeTitle: "미디어 미리보기 꺼짐", safeBody: "NSFW 모드를 켜야 원격 이미지를 불러옵니다. 텍스트와 작업 제어는 계속 사용할 수 있습니다.",
  },
  fr: {
    label: "Mode NSFW", enabled: "Le mode NSFW est activé", disabled: "Le mode NSFW est désactivé", description: "Afficher les médias des créateurs et des œuvres pouvant contenir du contenu explicite.", change: "Modifier le mode multimédia NSFW", confirmTitle: "Activer les aperçus NSFW ?", confirmBody: "Les avatars, bannières, couvertures, pièces jointes et images du contenu peuvent contenir des éléments explicites.", confirmPersistence: "Ce choix reste actif dans ce navigateur jusqu’à sa désactivation.", confirmNetwork: "KToolBox demandera les médias via son proxy authentifié de même origine.", confirmAction: "Activer le mode NSFW", unavailable: "Aperçu indisponible", tooLarge: "Cette image est trop volumineuse pour être prévisualisée.", unsupported: "Ce fichier n’est pas une image compatible.", retry: "Réessayer l’aperçu", gallery: "Galerie multimédia", cover: "Couverture", loadMore: "Afficher 12 images de plus", viewer: "Visionneuse de médias", previous: "Image précédente", next: "Image suivante", imagePosition: "Image {{current}} sur {{total}}", coverAlt: "Couverture de {{title}}", avatarAlt: "Avatar de {{name}}", bannerAlt: "Bannière de {{name}}", mediaAlt: "Aperçu multimédia {{index}}", safeTitle: "Les aperçus sont désactivés", safeBody: "Activez le mode NSFW pour charger les images distantes. Le texte et les commandes restent disponibles.",
  },
  ru: {
    label: "Режим NSFW", enabled: "Режим NSFW включён", disabled: "Режим NSFW выключен", description: "Показывать медиа авторов и работ, которые могут содержать материалы для взрослых.", change: "Изменить режим медиа NSFW", confirmTitle: "Включить предпросмотр NSFW?", confirmBody: "Аватары, баннеры, обложки, вложения и изображения в тексте могут содержать материалы для взрослых.", confirmPersistence: "Настройка сохранится в этом браузере, пока вы её не отключите.", confirmNetwork: "KToolBox будет загружать медиа через аутентифицированный прокси того же источника.", confirmAction: "Включить режим NSFW", unavailable: "Предпросмотр недоступен", tooLarge: "Изображение слишком велико для предпросмотра.", unsupported: "Этот файл не поддерживается как изображение предпросмотра.", retry: "Повторить предпросмотр", gallery: "Галерея медиа", cover: "Обложка", loadMore: "Показать ещё 12", viewer: "Просмотр медиа", previous: "Предыдущее изображение", next: "Следующее изображение", imagePosition: "Изображение {{current}} из {{total}}", coverAlt: "Обложка {{title}}", avatarAlt: "Аватар {{name}}", bannerAlt: "Баннер {{name}}", mediaAlt: "Предпросмотр медиа {{index}}", safeTitle: "Предпросмотр медиа выключен", safeBody: "Включите режим NSFW, чтобы загружать удалённые изображения. Текст и управление задачами остаются доступны.",
  },
} as const satisfies Record<string, TranslationShape<typeof en>>;
