'use strict';

/*
 * ============================================================
 * ASCII LAB — FRONTEND APPLICATION
 * Image + Video + Webcam
 * ============================================================
 */

const API_URL = '';

const CONFIG = {
  renderDebounce: 180,

  minZoom: 4,
  maxZoom: 24,
  defaultZoom: 8,

  maxImageSize: 25 * 1024 * 1024,
  maxVideoSize: 100 * 1024 * 1024,

  supportedImageTypes: [
    'image/jpeg',
    'image/png',
    'image/webp'
  ],

  supportedImageExtensions: [
    '.jpg',
    '.jpeg',
    '.png',
    '.webp'
  ],

  supportedVideoTypes: [
    'video/mp4',
    'video/webm',
    'video/quicktime',
    'video/x-msvideo',
    'video/x-matroska'
  ],

  supportedVideoExtensions: [
    '.mp4',
    '.webm',
    '.mov',
    '.avi',
    '.mkv'
  ],

  webcamFPS: 8,
  webcamJPEGQuality: 0.72
};


/* ============================================================
   STATE
   ============================================================ */

const state = {
  currentFile: null,

  gallery: [],

  currentAscii: '',

  currentResult: null,

  zoomLevel: CONFIG.defaultZoom,

  debounceTimer: null,

  renderController: null,

  renderRequestId: 0,

  isRendering: false,

  currentMediaMode: 'image',

  /* Video */
  videoFrames: [],
  videoPlaying: false,
  videoAnimationId: null,
  videoStartTime: 0,

  /* Webcam */
  webcamStream: null,
  webcamRunning: false,
  webcamTimer: null,
  webcamCanvas: null,

  /* Current request */
  mediaRequestId: 0
};


/* ============================================================
   DEMO ASCII
   ============================================================ */

const DEMO_ASCII = `                    .-++===+++==--.
                .-+**##############**+-.
             .-+**####%%%%%%%%%%%%####**+-.
           .-+**####%%%%%%%%%%%%%%%%%%####**+-.
         .-+**####%%%%%%%%%%%%%%%%%%%%%%####**+-.
        .+**####%%%%%%%%%%%%%%%%%%%%%%%%%%####**+.
       .+**####%%%%%%%%%%%%%%%%%%%%%%%%%%%%####**+.
      .+**####%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%####**+.
     .+**####%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%####**+.
    .+**####%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%####**+.
    .+**####%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%####**+.
   .+**####%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%####**+.
   .+**####%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%####**+.
   .+**####%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%####**+.
   .+**####%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%####**+.
    .+**####%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%####**+.
    .+**####%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%####**+.
     .+**####%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%####**+.
      .+**####%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%####**+.
       .+**####%%%%%%%%%%%%%%%%%%%%%%%%%%%%####**+.
        .+**####%%%%%%%%%%%%%%%%%%%%%%%%%%####**+.
         .-+**####%%%%%%%%%%%%%%%%%%%%%%####**+-.
           .-+**####%%%%%%%%%%%%%%%%%%####**+-.
             .-+**####%%%%%%%%%%%%####**+-.
                .-+**##############**+-.
                    .-++===+++==--.`;


/* ============================================================
   DOM
   ============================================================ */

const $ = id => document.getElementById(id);

const els = {
  landingView: $('landingView'),
  editorView: $('editorView'),

  heroAscii: $('heroAscii'),

  fileInput: $('fileInput'),
  dropZone: $('dropZone'),

  asciiOutput: $('asciiOutput'),

  emptyState: $('emptyState'),
  loadingState: $('loadingState'),

  previewContainer: $('previewContainer'),

  fileName: $('fileName'),

  galleryGrid: $('galleryGrid'),

  exportModal: $('exportModal'),
  exportPreview: $('exportPreview'),

  toast: $('toast'),

  previewDims: $('previewDims'),
  previewMode: $('previewMode'),

  statTime: $('statTime'),
  statDims: $('statDims'),
  statChars: $('statChars'),

  modeSelector: $('modeSelector'),

  charsetSelect: $('charsetSelect'),
  customCharset: $('customCharset'),

  widthRange: $('widthRange'),
  widthVal: $('widthVal'),

  brightnessRange: $('brightnessRange'),
  brightnessVal: $('brightnessVal'),

  contrastRange: $('contrastRange'),
  contrastVal: $('contrastVal'),

  gammaRange: $('gammaRange'),
  gammaVal: $('gammaVal'),

  ditherSelect: $('ditherSelect'),
  colorSelect: $('colorSelect'),

  invertCheck: $('invertCheck'),

  zoomIn: $('zoomIn'),
  zoomOut: $('zoomOut'),

  copyBtn: $('copyBtn'),
  exportBtn: $('exportBtn'),

  exportCopy: $('exportCopy'),
  exportTxt: $('exportTxt'),

  renderStatus: $('renderStatus'),

  galleryCount: $('galleryCount'),

  /* New optional elements */
  webcamVideo: $('webcamVideo'),
  webcamStart: $('webcamStart'),
  webcamStop: $('webcamStop'),
  webcamStatus: $('webcamStatus')
};


/* ============================================================
   INITIALIZATION
   ============================================================ */

document.addEventListener('DOMContentLoaded', initialize);

function initialize() {

  if (els.heroAscii) {
    els.heroAscii.textContent = DEMO_ASCII;
  }

  updateLabels();
  updateGalleryCount();
  updateZoom();

  bindEvents();

  showLanding();
}


/* ============================================================
   EVENTS
   ============================================================ */

function bindEvents() {

  /* ---------------- Upload ---------------- */

  els.dropZone?.addEventListener('click', () => {

    if (state.currentMediaMode === 'webcam') {
      startWebcam();
      return;
    }

    els.fileInput?.click();
  });


  els.dropZone?.addEventListener('keydown', event => {

    if (event.key !== 'Enter' && event.key !== ' ') {
      return;
    }

    event.preventDefault();

    if (state.currentMediaMode === 'webcam') {
      startWebcam();
    } else {
      els.fileInput?.click();
    }
  });


  els.dropZone?.addEventListener('dragover', event => {

    event.preventDefault();

    if (
      event.dataTransfer &&
      event.dataTransfer.types.includes('Files')
    ) {
      els.dropZone.classList.add('dragover');
    }
  });


  els.dropZone?.addEventListener('dragleave', () => {
    els.dropZone.classList.remove('dragover');
  });


  els.dropZone?.addEventListener('drop', handleDrop);


  els.fileInput?.addEventListener('change', event => {

    const file = event.target.files?.[0];

    if (file) {
      handleFile(file);
    }

    event.target.value = '';
  });


  /* ---------------- Media modes ---------------- */

  document.querySelectorAll('.media-mode').forEach(button => {

    button.addEventListener('click', () => {

      setMediaMode(button.dataset.media);
    });
  });


  /* ---------------- Rendering modes ---------------- */

  els.modeSelector?.querySelectorAll('.mode-btn').forEach(button => {

    button.addEventListener('click', () => {

      setMode(button.dataset.mode);
    });
  });


  /* ---------------- Charset ---------------- */

  els.charsetSelect?.addEventListener('change', () => {

    const isCustom =
      els.charsetSelect.value === 'CUSTOM';

    els.customCharset?.classList.toggle(
      'hidden',
      !isCustom
    );

    debouncedRender();
  });


  els.customCharset?.addEventListener(
    'input',
    debouncedRender
  );


  /* ---------------- Sliders ---------------- */

  [
    els.widthRange,
    els.brightnessRange,
    els.contrastRange,
    els.gammaRange
  ]
    .filter(Boolean)
    .forEach(element => {

      element.addEventListener(
        'input',
        updateLabels
      );

      element.addEventListener(
        'change',
        debouncedRender
      );
    });


  /* ---------------- Selects ---------------- */

  [
    els.ditherSelect,
    els.colorSelect,
    els.invertCheck
  ]
    .filter(Boolean)
    .forEach(element => {

      element.addEventListener(
        'change',
        debouncedRender
      );
    });


  /* ---------------- Toolbar ---------------- */

  els.zoomIn?.addEventListener(
    'click',
    () => setZoom(state.zoomLevel + 1)
  );

  els.zoomOut?.addEventListener(
    'click',
    () => setZoom(state.zoomLevel - 1)
  );

  els.copyBtn?.addEventListener(
    'click',
    copyToClipboard
  );

  els.exportBtn?.addEventListener(
    'click',
    openExport
  );

  els.exportCopy?.addEventListener(
    'click',
    copyToClipboard
  );

  els.exportTxt?.addEventListener(
    'click',
    downloadTxt
  );


  /* ---------------- Webcam ---------------- */

  els.webcamStart?.addEventListener(
    'click',
    startWebcam
  );

  els.webcamStop?.addEventListener(
    'click',
    stopWebcam
  );


  /* ---------------- Keyboard ---------------- */

  document.addEventListener(
    'keydown',
    handleKeyboard
  );
}


/* ============================================================
   KEYBOARD
   ============================================================ */

function handleKeyboard(event) {

  if (event.key === 'Escape') {

    closeExport();

    if (state.currentMediaMode === 'webcam') {
      stopWebcam();
    }

    return;
  }

  const tag = event.target?.tagName;

  if (
    tag === 'INPUT' ||
    tag === 'TEXTAREA' ||
    tag === 'SELECT'
  ) {
    return;
  }

  if (
    (event.ctrlKey || event.metaKey) &&
    event.key.toLowerCase() === 'o'
  ) {

    event.preventDefault();

    els.fileInput?.click();
  }

  if (
    (event.ctrlKey || event.metaKey) &&
    event.key.toLowerCase() === 'c' &&
    state.currentAscii
  ) {

    event.preventDefault();

    copyToClipboard();
  }
}


/* ============================================================
   VIEW SWITCHING
   ============================================================ */

function showEditor() {

  els.landingView?.classList.add('hidden');

  els.editorView?.classList.remove('hidden');

  requestAnimationFrame(() => {

    els.previewContainer?.focus?.({
      preventScroll: true
    });
  });
}


function showLanding() {

  stopAllMedia();

  els.editorView?.classList.add('hidden');

  els.landingView?.classList.remove('hidden');
}


function triggerUpload() {

  showEditor();

  setMediaMode('image');

  requestAnimationFrame(() => {

    els.fileInput?.click();
  });
}


/* ============================================================
   MEDIA MODE
   ============================================================ */

function setMediaMode(mode) {

  const supportedModes = [
    'image',
    'video',
    'webcam'
  ];

  if (!supportedModes.includes(mode)) {
    return;
  }

  /*
   * Stop whatever was previously running.
   */
  stopVideoPlayback();
  stopWebcam();

  cancelCurrentRender();

  state.currentMediaMode = mode;

  /*
   * Update active media mode button.
   */
  document.querySelectorAll('.media-mode').forEach(button => {

    button.classList.toggle(
      'active',
      button.dataset.media === mode
    );
  });

  /*
   * Hide/show the webcam container.
   */
  const webcamContainer =
    document.getElementById(
      'webcamContainer'
    );

  if (webcamContainer) {

    webcamContainer.classList.toggle(
      'hidden',
      mode !== 'webcam'
    );
  }

  /*
   * IMAGE MODE
   */

  if (mode === 'image') {

    configureFileInput('image');

    updateUploadUI();

    if (state.currentFile &&
        isImageFile(state.currentFile)) {

      renderImage();
    } else {

      state.currentFile = null;

      showEmpty();
    }

    return;
  }


  /*
   * VIDEO MODE
   */

  if (mode === 'video') {

    configureFileInput('video');

    updateUploadUI();

    if (
      state.currentFile &&
      isVideoFile(state.currentFile)
    ) {

      renderVideo();
    } else {

      state.currentFile = null;

      showEmpty();

      showToast(
        'Select a video file to begin'
      );
    }

    return;
  }


  /*
   * WEBCAM MODE
   */

  if (mode === 'webcam') {

    configureFileInput('webcam');

    updateUploadUI();

    createWebcamUI();

    showToast(
      'Click Start Camera to begin'
    );
  }
}


/* ============================================================
   FILE INPUT
   ============================================================ */

function configureFileInput(mode) {

  if (!els.fileInput) {
    return;
  }

  if (mode === 'image') {

    els.fileInput.accept =
      'image/jpeg,image/png,image/webp';

  } else if (mode === 'video') {

    els.fileInput.accept =
      'video/mp4,video/webm,video/quicktime,video/x-msvideo,video/x-matroska';

  } else {

    els.fileInput.accept =
      'image/jpeg,image/png,image/webp,video/mp4,video/webm';
  }
}


/* ============================================================
   UPLOAD UI
   ============================================================ */

function updateUploadUI() {

  if (!els.dropZone) {
    return;
  }

  const title =
    els.dropZone.querySelector('.upload-title');

  const hint =
    els.dropZone.querySelector('.upload-hint');

  const formats =
    els.dropZone.querySelector('.upload-formats');

  if (!title || !hint || !formats) {
    return;
  }


  if (state.currentMediaMode === 'image') {

    title.textContent =
      'Drop image here';

    hint.textContent =
      'or click to browse';

    formats.textContent =
      'JPG · PNG · WEBP';

    return;
  }


  if (state.currentMediaMode === 'video') {

    title.textContent =
      'Drop video here';

    hint.textContent =
      'or click to browse';

    formats.textContent =
      'MP4 · WEBM · MOV · AVI · MKV';

    return;
  }


  if (state.currentMediaMode === 'webcam') {

    title.textContent =
      'Start camera';

    hint.textContent =
      'or click here';

    formats.textContent =
      'Browser camera access';
  }
}


/* ============================================================
   FILE VALIDATION
   ============================================================ */

function validateFile(file) {

  if (!file) {

    return {
      valid: false,
      message: 'No file selected'
    };
  }


  if (state.currentMediaMode === 'image') {

    const extension =
      getExtension(file.name);

    const validType =
      CONFIG.supportedImageTypes.includes(
        file.type
      );

    const validExtension =
      CONFIG.supportedImageExtensions.includes(
        extension
      );

    if (!validType && !validExtension) {

      return {
        valid: false,
        message:
          'Only JPG, PNG, and WebP images are supported'
      };
    }


    if (file.size > CONFIG.maxImageSize) {

      return {
        valid: false,
        message:
          'Image is too large. Maximum size is 25 MB'
      };
    }

    return { valid: true };
  }


  if (state.currentMediaMode === 'video') {

    const extension =
      getExtension(file.name);

    const validType =
      CONFIG.supportedVideoTypes.includes(
        file.type
      );

    const validExtension =
      CONFIG.supportedVideoExtensions.includes(
        extension
      );

    if (!validType && !validExtension) {

      return {
        valid: false,
        message:
          'Only MP4, WebM, MOV, AVI, and MKV videos are supported'
      };
    }


    if (file.size > CONFIG.maxVideoSize) {

      return {
        valid: false,
        message:
          'Video is too large. Maximum size is 100 MB'
      };
    }

    return { valid: true };
  }


  return {
    valid: false,
    message:
      'Webcam mode does not require a file'
  };
}


function validateImageFile(file) {

  const previousMode =
    state.currentMediaMode;

  state.currentMediaMode = 'image';

  const result = validateFile(file);

  state.currentMediaMode = previousMode;

  return result;
}


function getExtension(filename) {

  const index =
    filename.lastIndexOf('.');

  if (index === -1) {
    return '';
  }

  return filename
    .slice(index)
    .toLowerCase();
}


function isImageFile(file) {

  if (!file) {
    return false;
  }

  return (
    CONFIG.supportedImageTypes.includes(file.type) ||
    CONFIG.supportedImageExtensions.includes(
      getExtension(file.name)
    )
  );
}


function isVideoFile(file) {

  if (!file) {
    return false;
  }

  return (
    CONFIG.supportedVideoTypes.includes(file.type) ||
    CONFIG.supportedVideoExtensions.includes(
      getExtension(file.name)
    )
  );
}


/* ============================================================
   FILE HANDLING
   ============================================================ */

function handleDrop(event) {

  event.preventDefault();

  els.dropZone?.classList.remove(
    'dragover'
  );

  if (
    state.currentMediaMode === 'webcam'
  ) {

    startWebcam();

    return;
  }

  const file =
    event.dataTransfer?.files?.[0];

  if (!file) {
    return;
  }

  handleFile(file);
}


function handleFile(file) {

  const validation =
    validateFile(file);

  if (!validation.valid) {

    showToast(
      validation.message,
      'error'
    );

    return;
  }


  cancelCurrentRender();

  stopVideoPlayback();
  stopWebcam();


  state.currentFile = file;

  addToGallery(file);


  if (els.fileName) {

    els.fileName.textContent =
      file.name;
  }


  showEditor();


  if (
    state.currentMediaMode === 'video'
  ) {

    renderVideo();

  } else {

    renderImage();
  }
}


/* ============================================================
   GALLERY
   ============================================================ */

function addToGallery(file) {

  const existingIndex =
    state.gallery.findIndex(item =>

      item.file.name === file.name &&
      item.file.size === file.size &&
      item.file.lastModified ===
        file.lastModified
    );


  if (existingIndex !== -1) {

    state.currentFile =
      state.gallery[existingIndex].file;

    refreshGallery();

    return;
  }


  const url =
    URL.createObjectURL(file);

  state.gallery.push({
    file,
    url
  });

  refreshGallery();
}


function refreshGallery() {

  if (!els.galleryGrid) {
    return;
  }

  els.galleryGrid.innerHTML = '';


  state.gallery.forEach(
    (item, index) => {

      const wrapper =
        document.createElement('div');

      wrapper.className =
        'gallery-item';


      if (
        item.file === state.currentFile
      ) {

        wrapper.classList.add(
          'active'
        );
      }


      wrapper.setAttribute(
        'tabindex',
        '0'
      );

      wrapper.setAttribute(
        'role',
        'button'
      );


      wrapper.setAttribute(
        'aria-label',
        `Select ${item.file.name}`
      );


      /*
       * Image thumbnail
       */

      if (isImageFile(item.file)) {

        const image =
          document.createElement('img');

        image.src =
          item.url;

        image.alt =
          `Preview of ${item.file.name}`;

        wrapper.appendChild(image);

      } else {

        /*
         * Video thumbnail
         */

        const video =
          document.createElement('video');

        video.src =
          item.url;

        video.muted = true;

        video.playsInline = true;

        video.preload = 'metadata';

        wrapper.appendChild(video);
      }


      const remove =
        document.createElement('button');

      remove.type = 'button';

      remove.className = 'remove';

      remove.textContent = '×';

      remove.setAttribute(
        'aria-label',
        `Remove ${item.file.name}`
      );


      remove.addEventListener(
        'click',
        event => {

          event.stopPropagation();

          removeFromGallery(index);
        }
      );


      wrapper.addEventListener(
        'click',
        () => {

          selectGalleryItem(index);
        }
      );


      wrapper.addEventListener(
        'keydown',
        event => {

          if (
            event.key === 'Enter' ||
            event.key === ' '
          ) {

            event.preventDefault();

            selectGalleryItem(index);
          }
        }
      );


      wrapper.appendChild(remove);

      els.galleryGrid.appendChild(
        wrapper
      );
    }
  );


  updateGalleryCount();
}


function selectGalleryItem(index) {

  const item =
    state.gallery[index];

  if (!item) {
    return;
  }


  cancelCurrentRender();

  stopVideoPlayback();
  stopWebcam();


  state.currentFile =
    item.file;


  if (els.fileName) {

    els.fileName.textContent =
      item.file.name;
  }


  /*
   * Automatically switch mode
   * based on selected file.
   */

  const mode =
    isVideoFile(item.file)
      ? 'video'
      : 'image';


  state.currentMediaMode =
    mode;


  document
    .querySelectorAll('.media-mode')
    .forEach(button => {

      button.classList.toggle(
        'active',
        button.dataset.media === mode
      );
    });


  configureFileInput(mode);

  updateUploadUI();

  refreshGallery();


  if (mode === 'video') {

    renderVideo();

  } else {

    renderImage();
  }
}


function removeFromGallery(index) {

  const item =
    state.gallery[index];

  if (!item) {
    return;
  }


  const wasCurrent =
    item.file === state.currentFile;


  URL.revokeObjectURL(
    item.url
  );


  state.gallery.splice(index, 1);


  if (wasCurrent) {

    const next =
      state.gallery[index] ||
      state.gallery[index - 1] ||
      state.gallery[0];


    state.currentFile =
      next?.file || null;


    if (els.fileName) {

      els.fileName.textContent =
        next?.file?.name ||
        'No image selected';
    }


    if (state.currentFile) {

      const mode =
        isVideoFile(state.currentFile)
          ? 'video'
          : 'image';

      state.currentMediaMode =
        mode;

      configureFileInput(mode);

      updateUploadUI();

      if (mode === 'video') {

        renderVideo();

      } else {

        renderImage();
      }

    } else {

      cancelCurrentRender();

      showEmpty();
    }
  }


  refreshGallery();
}


function updateGalleryCount() {

  if (!els.galleryCount) {
    return;
  }

  els.galleryCount.textContent =
    state.gallery.length;
}


/* ============================================================
   RENDER STATES
   ============================================================ */

function showEmpty() {

  els.emptyState?.classList.remove(
    'hidden'
  );

  els.loadingState?.classList.add(
    'hidden'
  );

  els.asciiOutput?.classList.add(
    'hidden'
  );


  if (els.asciiOutput) {

    els.asciiOutput.textContent =
      '';

    els.asciiOutput.innerHTML =
      '';
  }


  updateStats(null);

  setRenderStatus('READY');
}


function showLoading() {

  els.emptyState?.classList.add(
    'hidden'
  );

  els.loadingState?.classList.remove(
    'hidden'
  );

  els.asciiOutput?.classList.add(
    'hidden'
  );

  setRenderStatus(
    'RENDERING'
  );
}


function showOutput() {

  els.emptyState?.classList.add(
    'hidden'
  );

  els.loadingState?.classList.add(
    'hidden'
  );

  els.asciiOutput?.classList.remove(
    'hidden'
  );

  setRenderStatus(
    'READY'
  );
}


function setRenderStatus(status) {

  if (!els.renderStatus) {
    return;
  }

  els.renderStatus.textContent =
    status;
}


/* ============================================================
   IMAGE RENDERING
   ============================================================ */

async function renderImage() {

  if (!state.currentFile) {
    return;
  }


  if (!isImageFile(state.currentFile)) {
    return;
  }


  cancelCurrentRender();

  stopVideoPlayback();
  stopWebcam();


  const requestId =
    state.renderRequestId;


  const controller =
    new AbortController();


  state.renderController =
    controller;

  state.isRendering =
    true;


  showLoading();


  const formData =
    buildRenderFormData(
      state.currentFile
    );


  try {

    const response =
      await fetch(
        `${API_URL}/api/render/image`,
        {
          method: 'POST',
          body: formData,
          signal: controller.signal
        }
      );


    if (
      requestId !==
      state.renderRequestId
    ) {
      return;
    }


    if (!response.ok) {

      throw new Error(
        await parseAPIError(response)
      );
    }


    const data =
      await response.json();


    if (
      requestId !==
      state.renderRequestId
    ) {
      return;
    }


    displayResult(data);


  } catch (error) {

    if (
      error.name ===
      'AbortError'
    ) {
      return;
    }


    console.error(
      'Image render error:',
      error
    );


    showToast(
      error.message ||
        'Unable to render image',
      'error'
    );


    if (!state.currentAscii) {

      showEmpty();

    } else {

      showOutput();
    }


  } finally {

    if (
      requestId ===
      state.renderRequestId
    ) {

      state.isRendering =
        false;

      state.renderController =
        null;
    }
  }
}


/* ============================================================
   VIDEO RENDERING
   ============================================================ */

async function renderVideo() {

  if (!state.currentFile) {
    return;
  }


  if (!isVideoFile(state.currentFile)) {

    showToast(
      'Please select a video file',
      'error'
    );

    return;
  }


  cancelCurrentRender();

  stopVideoPlayback();
  stopWebcam();


  const requestId =
    state.renderRequestId;


  const controller =
    new AbortController();


  state.renderController =
    controller;


  state.isRendering =
    true;


  showLoading();


  const formData =
    buildRenderFormData(
      state.currentFile
    );


  /*
   * Backend uses this to reduce
   * the number of extracted frames.
   */

  formData.append(
    'target_fps',
    String(CONFIG.webcamFPS)
  );


  try {

    const response =
      await fetch(
        `${API_URL}/api/render/video/frames`,
        {
          method: 'POST',
          body: formData,
          signal: controller.signal
        }
      );


    if (
      requestId !==
      state.renderRequestId
    ) {
      return;
    }


    if (!response.ok) {

      throw new Error(
        await parseAPIError(response)
      );
    }


    const data =
      await response.json();


    if (
      requestId !==
      state.renderRequestId
    ) {
      return;
    }


    if (
      !Array.isArray(data.frames) ||
      data.frames.length === 0
    ) {

      throw new Error(
        'The server returned no video frames'
      );
    }


    state.videoFrames =
      data.frames;


    state.currentAscii =
      data.frames[0].ascii || '';


    state.currentResult =
      data.frames[0];


    showOutput();


    displayVideoFrame(
      data.frames[0]
    );


    updateVideoStats(data);


    startVideoPlayback();


  } catch (error) {

    if (
      error.name ===
      'AbortError'
    ) {
      return;
    }


    console.error(
      'Video render error:',
      error
    );


    showToast(
      error.message ||
        'Unable to render video',
      'error'
    );


    showEmpty();


  } finally {

    if (
      requestId ===
      state.renderRequestId
    ) {

      state.isRendering =
        false;

      state.renderController =
        null;
    }
  }
}


/* ============================================================
   VIDEO PLAYBACK
   ============================================================ */

function startVideoPlayback() {

  stopVideoPlayback();


  if (
    !state.videoFrames.length
  ) {
    return;
  }


  state.videoPlaying =
    true;


  state.videoStartTime =
    performance.now();


  setRenderStatus(
    'PLAYING'
  );


  state.videoAnimationId =
    requestAnimationFrame(
      videoAnimationLoop
    );
}


function videoAnimationLoop(now) {

  if (
    !state.videoPlaying ||
    state.currentMediaMode !==
      'video'
  ) {
    return;
  }


  const frames =
    state.videoFrames;


  if (!frames.length) {
    return;
  }


  const elapsed =
    (now - state.videoStartTime) /
    1000;


  const duration =
    frames[frames.length - 1]
      .timestamp;


  /*
   * Loop video.
   */

  let currentTime =
    duration > 0
      ? elapsed % duration
      : 0;


  let frame =
    frames[0];


  for (
    let i = 0;
    i < frames.length;
    i++
  ) {

    if (
      frames[i].timestamp <=
      currentTime
    ) {

      frame =
        frames[i];

    } else {

      break;
    }
  }


  displayVideoFrame(frame);


  state.videoAnimationId =
    requestAnimationFrame(
      videoAnimationLoop
    );
}


function stopVideoPlayback() {

  state.videoPlaying =
    false;


  if (
    state.videoAnimationId !== null
  ) {

    cancelAnimationFrame(
      state.videoAnimationId
    );

    state.videoAnimationId =
      null;
  }
}


function displayVideoFrame(frame) {

  if (!frame) {
    return;
  }


  state.currentAscii =
    frame.ascii || '';


  state.currentResult =
    frame;


  const isColor =
    Array.isArray(frame.color_data) &&
    els.colorSelect?.value !==
      'monochrome';


  if (isColor) {

    renderColorASCII(frame);

  } else {

    els.asciiOutput.innerHTML =
      '';

    els.asciiOutput.textContent =
      frame.ascii || '';

    els.asciiOutput.classList.remove(
      'color-mode'
    );
  }


  const width =
    frame.width ?? '—';

  const height =
    frame.height ?? '—';


  if (els.previewDims) {

    els.previewDims.textContent =
      `${width}×${height}`;
  }


  if (els.previewMode) {

    els.previewMode.textContent =
      capitalize(
        frame.mode ||
          getMode()
      );
  }


  if (els.statChars) {

    els.statChars.textContent =
      (
        Number(width) *
        Number(height)
      ).toLocaleString();
  }


  updateZoom();
}


function updateVideoStats(data) {

  if (els.statTime) {

    els.statTime.textContent =
      `${data.total_frames} frames`;
  }


  if (
    els.statDims &&
    data.frames?.[0]
  ) {

    const frame =
      data.frames[0];

    els.statDims.textContent =
      `${frame.width}×${frame.height}`;
  }


  if (
    els.statChars &&
    data.frames?.[0]
  ) {

    const frame =
      data.frames[0];

    els.statChars.textContent =
      (
        Number(frame.width) *
        Number(frame.height)
      ).toLocaleString();
  }
}


/* ============================================================
   WEBCAM UI
   ============================================================ */

function createWebcamUI() {

  /*
   * Get the static container from HTML.
   */

  const container =
    document.getElementById(
      'webcamContainer'
    );

  if (!container) {
    console.error('Webcam container not found in DOM');
    return;
  }

  /*
   * Clear any existing content.
   */

  container.innerHTML = '';

  /*
   * Create video element.
   */

  const video =
    document.createElement('video');

  video.id =
    'webcamVideo';

  video.autoplay =
    true;

  video.muted =
    true;

  video.playsInline =
    true;

  video.style.width =
    '100%';

  video.style.maxWidth =
    '640px';

  video.style.display =
    'block';

  /*
   * Create controls.
   */

  const controls =
    document.createElement('div');

  controls.className =
    'webcam-controls';

  /*
   * Create Start button.
   */

  const start =
    document.createElement('button');

  start.type =
    'button';

  start.id =
    'webcamStart';

  start.className =
    'btn btn-primary';

  start.textContent =
    'Start Camera';

  start.addEventListener(
    'click',
    startWebcam
  );

  /*
   * Create Stop button.
   */

  const stop =
    document.createElement('button');

  stop.type =
    'button';

  stop.id =
    'webcamStop';

  stop.className =
    'btn btn-ghost';

  stop.textContent =
    'Stop Camera';

  stop.addEventListener(
    'click',
    stopWebcam
  );

  /*
   * Create status indicator.
   */

  const status =
    document.createElement('span');

  status.id =
    'webcamStatus';

  status.className =
    'webcam-status';

  status.textContent =
    'Camera stopped';

  /*
   * Build controls layout.
   */

  controls.appendChild(start);
  controls.appendChild(stop);
  controls.appendChild(status);

  /*
   * Add to container.
   */

  container.appendChild(video);
  container.appendChild(controls);

  /*
   * Update element references for later access.
   */

  els.webcamVideo =
    video;

  els.webcamStart =
    start;

  els.webcamStop =
    stop;

  els.webcamStatus =
    status;
}


/* ============================================================
   WEBCAM
   ============================================================ */

async function startWebcam() {

  if (
    state.currentMediaMode !==
    'webcam'
  ) {
    setMediaMode('webcam');
  }


  if (
    !navigator.mediaDevices ||
    !navigator.mediaDevices.getUserMedia
  ) {

    showToast(
      'Camera access requires HTTPS or localhost',
      'error'
    );

    return;
  }


  if (state.webcamRunning) {
    return;
  }


  createWebcamUI();


  try {

    state.webcamStream =
      await navigator.mediaDevices.getUserMedia(
        {
          video: {
            width: {
              ideal: 640
            },

            height: {
              ideal: 480
            },

            facingMode: 'user'
          },

          audio: false
        }
      );


    if (!els.webcamVideo) {

      throw new Error(
        'Webcam video element is missing'
      );
    }


    els.webcamVideo.srcObject =
      state.webcamStream;


    await els.webcamVideo.play();


    state.webcamRunning =
      true;


    if (els.webcamStatus) {

      els.webcamStatus.textContent =
        'Camera running';
    }


    setRenderStatus(
      'WEBCAM'
    );


    showToast(
      'Camera started'
    );


    /*
     * Create canvas once.
     */

    if (!state.webcamCanvas) {

      state.webcamCanvas =
        document.createElement(
          'canvas'
        );
    }


    /*
     * Begin frame processing.
     */

    scheduleWebcamFrame();


  } catch (error) {

    console.error(
      'Webcam error:',
      error
    );


    let message =
      'Unable to access webcam';


    if (
      error.name ===
      'NotAllowedError'
    ) {

      message =
        'Camera permission was denied. Allow camera access in your browser.';

    } else if (
      error.name ===
      'NotFoundError'
    ) {

      message =
        'No camera was found on this device.';

    } else if (
      error.name ===
      'NotReadableError'
    ) {

      message =
        'Camera is already being used by another application.';

    } else if (
      error.name ===
      'SecurityError'
    ) {

      message =
        'Camera access is blocked by browser security settings.';
    }


    showToast(
      message,
      'error'
    );


    stopWebcam();
  }
}


function scheduleWebcamFrame() {

  if (
    !state.webcamRunning
  ) {
    return;
  }


  const interval =
    1000 / CONFIG.webcamFPS;


  state.webcamTimer =
    setTimeout(
      async () => {

        await processWebcamFrame();

        scheduleWebcamFrame();

      },
      interval
    );
}


async function processWebcamFrame() {

  if (
    !state.webcamRunning ||
    !els.webcamVideo ||
    !state.webcamCanvas
  ) {
    return;
  }


  if (
    els.webcamVideo.readyState <
    HTMLMediaElement.HAVE_CURRENT_DATA
  ) {
    return;
  }


  const video =
    els.webcamVideo;


  const canvas =
    state.webcamCanvas;


  const width =
    video.videoWidth || 640;

  const height =
    video.videoHeight || 480;


  /*
   * Reduce webcam upload size.
   */

  const maxWidth = 640;

  const scale =
    Math.min(
      1,
      maxWidth / width
    );


  canvas.width =
    Math.round(width * scale);

  canvas.height =
    Math.round(height * scale);


  const context =
    canvas.getContext(
      '2d',
      {
        willReadFrequently: true
      }
    );


  /*
   * Mirror webcam preview
   * so it behaves like a normal
   * front-facing camera.
   */

  context.save();

  context.translate(
    canvas.width,
    0
  );

  context.scale(
    -1,
    1
  );


  context.drawImage(
    video,
    0,
    0,
    canvas.width,
    canvas.height
  );


  context.restore();


  const blob =
    await canvasToBlob(
      canvas,
      'image/jpeg',
      CONFIG.webcamJPEGQuality
    );


  if (!blob) {
    return;
  }


  const formData =
    buildRenderFormData(blob);


  const requestId =
    ++state.mediaRequestId;


  try {

    const response =
      await fetch(
        `${API_URL}/api/render/webcam`,
        {
          method: 'POST',
          body: formData
        }
      );


    /*
     * Ignore old webcam responses.
     */

    if (
      requestId !==
      state.mediaRequestId
    ) {
      return;
    }


    if (!response.ok) {

      throw new Error(
        await parseAPIError(response)
      );
    }


    const data =
      await response.json();


    if (
      requestId !==
      state.mediaRequestId
    ) {
      return;
    }


    displayResult(data);


    if (els.statTime) {

      els.statTime.textContent =
        'LIVE';
    }


    setRenderStatus(
      'WEBCAM'
    );


  } catch (error) {

    console.error(
      'Webcam frame error:',
      error
    );

    /*
     * Don't display a toast for every
     * failed frame because that would
     * spam the UI.
     */

    if (
      state.webcamRunning
    ) {

      setRenderStatus(
        'CAMERA ERROR'
      );
    }
  }
}


function canvasToBlob(
  canvas,
  type,
  quality
) {

  return new Promise(
    resolve => {

      canvas.toBlob(
        blob => resolve(blob),
        type,
        quality
      );
    }
  );
}


function stopWebcam() {

  state.webcamRunning =
    false;


  state.mediaRequestId++;


  if (
    state.webcamTimer
  ) {

    clearTimeout(
      state.webcamTimer
    );

    state.webcamTimer =
      null;
  }


  if (
    state.webcamStream
  ) {

    state.webcamStream
      .getTracks()
      .forEach(track => {

        track.stop();
      });

    state.webcamStream =
      null;
  }


  if (
    els.webcamVideo
  ) {

    els.webcamVideo.srcObject =
      null;
  }


  if (
    els.webcamStatus
  ) {

    els.webcamStatus.textContent =
      'Camera stopped';
  }


  if (
    state.currentMediaMode ===
    'webcam'
  ) {

    setRenderStatus(
      'READY'
    );
  }
}


/* ============================================================
   STOP ALL MEDIA
   ============================================================ */

function stopAllMedia() {

  stopVideoPlayback();

  stopWebcam();

  cancelCurrentRender();
}


/* ============================================================
   BUILD FORM DATA
   ============================================================ */

function buildRenderFormData(file) {

  const formData =
    new FormData();


  formData.append(
    'file',
    file
  );


  formData.append(
    'width',
    els.widthRange?.value ||
      '80'
  );


  formData.append(
    'mode',
    getMode()
  );


  let charset =
    els.charsetSelect?.value ||
    'STANDARD';


  if (
    charset === 'CUSTOM'
  ) {

    charset =
      els.customCharset?.value ||
      '@%#*+=-:. ';
  }


  formData.append(
    'charset',
    charset
  );


  formData.append(
    'brightness',
    els.brightnessRange?.value ||
      '1'
  );


  formData.append(
    'contrast',
    els.contrastRange?.value ||
      '1'
  );


  formData.append(
    'gamma',
    els.gammaRange?.value ||
      '1'
  );


  formData.append(
    'invert',
    els.invertCheck?.checked
      ? 'true'
      : 'false'
  );


  formData.append(
    'dither',
    els.ditherSelect?.value ||
      'none'
  );


  formData.append(
    'color',
    els.colorSelect?.value ||
      'monochrome'
  );


  return formData;
}


/* ============================================================
   RENDERING CONTROLS
   ============================================================ */

function setMode(mode) {

  els.modeSelector
    ?.querySelectorAll('.mode-btn')
    .forEach(button => {

      button.classList.toggle(
        'active',
        button.dataset.mode ===
          mode
      );
    });


  debouncedRender();
}


function getMode() {

  const active =
    els.modeSelector
      ?.querySelector(
        '.mode-btn.active'
      );


  return (
    active?.dataset.mode ||
    'density'
  );
}


/* ============================================================
   CONTROL LABELS
   ============================================================ */

function updateLabels() {

  if (els.widthRange) {

    els.widthVal.textContent =
      els.widthRange.value;
  }


  if (els.brightnessRange) {

    els.brightnessVal.textContent =
      els.brightnessRange.value;
  }


  if (els.contrastRange) {

    els.contrastVal.textContent =
      els.contrastRange.value;
  }


  if (els.gammaRange) {

    els.gammaVal.textContent =
      els.gammaRange.value;
  }
}


/* ============================================================
   DEBOUNCE
   ============================================================ */

function debouncedRender() {

  clearTimeout(
    state.debounceTimer
  );


  state.debounceTimer =
    setTimeout(
      () => {

        if (
          state.currentMediaMode ===
          'image'
        ) {

          renderImage();

        } else if (
          state.currentMediaMode ===
          'video'
        ) {

          /*
           * Re-render uploaded video
           * when a control changes.
           */

          renderVideo();

        }
      },
      CONFIG.renderDebounce
    );
}


/* ============================================================
   RENDER CANCELLATION
   ============================================================ */

function cancelCurrentRender() {

  if (
    state.renderController
  ) {

    state.renderController.abort();

    state.renderController =
      null;
  }


  state.renderRequestId++;

  state.isRendering =
    false;
}


/* ============================================================
   API ERROR
   ============================================================ */

async function parseAPIError(response) {

  try {

    const data =
      await response.json();


    const detail =
      data?.detail;


    if (
      typeof detail ===
      'string'
    ) {

      return detail;
    }


    if (
      detail &&
      typeof detail ===
      'object'
    ) {

      return (
        detail.message ||
        detail.error ||
        detail.detail ||
        `Request failed (${response.status})`
      );
    }


    if (data?.message) {

      return data.message;
    }


  } catch {
    /* Non-JSON response */
  }


  return `Request failed (${response.status})`;
}


/* ============================================================
   DISPLAY RESULT
   ============================================================ */

function displayResult(data) {

  if (
    !data ||
    typeof data.ascii !==
      'string'
  ) {

    throw new Error(
      'Server returned an invalid ASCII response'
    );
  }


  state.currentAscii =
    data.ascii;


  state.currentResult =
    data;


  showOutput();


  const isColor =
    Array.isArray(
      data.color_data
    ) &&
    els.colorSelect?.value !==
      'monochrome';


  if (isColor) {

    renderColorASCII(data);

  } else {

    els.asciiOutput.innerHTML =
      '';

    els.asciiOutput.textContent =
      data.ascii;

    els.asciiOutput.classList.remove(
      'color-mode'
    );
  }


  const width =
    data.width ?? '—';

  const height =
    data.height ?? '—';


  const mode =
    data.mode ||
    getMode();


  if (els.previewDims) {

    els.previewDims.textContent =
      `${width}×${height}`;
  }


  if (els.previewMode) {

    els.previewMode.textContent =
      capitalize(mode);
  }


  updateStats(data);

  updateZoom();
}


/* ============================================================
   COLOR ASCII
   ============================================================ */

function renderColorASCII(data) {

  const lines =
    data.ascii.split('\n');

  const colors =
    data.color_data;


  els.asciiOutput.innerHTML =
    '';

  els.asciiOutput.classList.add(
    'color-mode'
  );


  const fragment =
    document.createDocumentFragment();


  lines.forEach(
    (line, y) => {

      const row =
        document.createElement(
          'div'
        );


      row.style.whiteSpace =
        'pre';


      for (
        let x = 0;
        x < line.length;
        x++
      ) {

        const span =
          document.createElement(
            'span'
          );


        span.textContent =
          line[x];


        const color =
          colors?.[y]?.[x];


        if (
          Array.isArray(color) &&
          color.length >= 3
        ) {

          const [
            r,
            g,
            b
          ] = color;


          span.style.color =
            `rgb(${r}, ${g}, ${b})`;
        }


        row.appendChild(
          span
        );
      }


      fragment.appendChild(
        row
      );
    }
  );


  els.asciiOutput.appendChild(
    fragment
  );
}


/* ============================================================
   STATISTICS
   ============================================================ */

function updateStats(data) {

  if (!data) {

    if (els.statTime) {
      els.statTime.textContent =
        '—';
    }

    if (els.statDims) {
      els.statDims.textContent =
        '—';
    }

    if (els.statChars) {
      els.statChars.textContent =
        '—';
    }

    return;
  }


  if (els.statTime) {

    const processing =
      Number(
        data.processing_ms
      );


    els.statTime.textContent =
      Number.isFinite(processing)
        ? `${processing.toFixed(
            processing % 1 === 0
              ? 0
              : 1
          )}ms`
        : '—';
  }


  if (
    els.statDims &&
    data.width &&
    data.height
  ) {

    els.statDims.textContent =
      `${data.width}×${data.height}`;
  }


  if (
    els.statChars &&
    data.width &&
    data.height
  ) {

    els.statChars.textContent =
      (
        Number(data.width) *
        Number(data.height)
      ).toLocaleString();
  }
}


/* ============================================================
   ZOOM
   ============================================================ */

function setZoom(value) {

  const next =
    Math.min(
      CONFIG.maxZoom,
      Math.max(
        CONFIG.minZoom,
        Number(value)
      )
    );


  state.zoomLevel =
    next;


  updateZoom();
}


function updateZoom() {

  if (!els.asciiOutput) {
    return;
  }


  const px =
    state.zoomLevel;


  els.asciiOutput.style.fontSize =
    `${px}px`;


  els.asciiOutput.style.lineHeight =
    `${px}px`;


  if (els.zoomOut) {

    els.zoomOut.disabled =
      px <= CONFIG.minZoom;
  }


  if (els.zoomIn) {

    els.zoomIn.disabled =
      px >= CONFIG.maxZoom;
  }
}


/* ============================================================
   EXPORT
   ============================================================ */

function openExport() {

  if (!state.currentAscii) {

    showToast(
      'Nothing to export yet',
      'error'
    );

    return;
  }


  if (els.exportPreview) {

    els.exportPreview.textContent =
      state.currentAscii;
  }


  els.exportModal?.classList.remove(
    'hidden'
  );
}


function closeExport() {

  els.exportModal?.classList.add(
    'hidden'
  );
}


/* ============================================================
   CLIPBOARD
   ============================================================ */

async function copyToClipboard() {

  if (!state.currentAscii) {

    showToast(
      'Nothing to copy yet',
      'error'
    );

    return;
  }


  try {

    if (
      navigator.clipboard &&
      window.isSecureContext
    ) {

      await navigator.clipboard.writeText(
        state.currentAscii
      );

    } else {

      const textarea =
        document.createElement(
          'textarea'
        );


      textarea.value =
        state.currentAscii;


      textarea.style.position =
        'fixed';

      textarea.style.opacity =
        '0';


      document.body.appendChild(
        textarea
      );


      textarea.select();


      const success =
        document.execCommand(
          'copy'
        );


      textarea.remove();


      if (!success) {

        throw new Error(
          'Clipboard access denied'
        );
      }
    }


    showToast(
      'ASCII copied to clipboard'
    );


    closeExport();


  } catch (error) {

    console.error(
      'Clipboard error:',
      error
    );


    showToast(
      'Copy failed — check browser permissions',
      'error'
    );
  }
}


/* ============================================================
   TXT DOWNLOAD
   ============================================================ */

function downloadTxt() {

  if (!state.currentAscii) {

    showToast(
      'Nothing to export yet',
      'error'
    );

    return;
  }


  const blob =
    new Blob(
      [state.currentAscii],
      {
        type:
          'text/plain;charset=utf-8'
      }
    );


  const url =
    URL.createObjectURL(blob);


  const anchor =
    document.createElement('a');


  anchor.href =
    url;


  anchor.download =
    `ascii-lab-${createFileTimestamp()}.txt`;


  document.body.appendChild(
    anchor
  );


  anchor.click();

  anchor.remove();


  setTimeout(
    () => URL.revokeObjectURL(url),
    1000
  );


  showToast(
    'Downloaded as .txt'
  );


  closeExport();
}


function createFileTimestamp() {

  const now =
    new Date();


  const pad =
    value =>
      String(value)
        .padStart(2, '0');


  return (
    [
      now.getFullYear(),
      pad(now.getMonth() + 1),
      pad(now.getDate())
    ].join('-') +
    '-' +
    [
      pad(now.getHours()),
      pad(now.getMinutes()),
      pad(now.getSeconds())
    ].join('')
  );
}


/* ============================================================
   TOAST
   ============================================================ */

function showToast(
  message,
  type = 'success'
) {

  if (!els.toast) {
    return;
  }


  els.toast.textContent =
    message;


  els.toast.className =
    'toast show' +
    (
      type === 'error'
        ? ' error'
        : ''
    );


  if (type === 'error') {

    els.toast.style.borderColor =
      'var(--danger)';

  } else {

    els.toast.style.borderColor =
      'var(--border)';
  }


  clearTimeout(
    els.toast._timer
  );


  els.toast._timer =
    setTimeout(
      () => {

        els.toast.classList.remove(
          'show'
        );

      },
      3000
    );
}


/* ============================================================
   UTILITIES
   ============================================================ */

function capitalize(value) {

  if (!value) {
    return '';
  }


  return (
    value.charAt(0).toUpperCase() +
    value.slice(1)
  );
}


/* ============================================================
   CLEANUP
   ============================================================ */

window.addEventListener(
  'beforeunload',
  () => {

    stopAllMedia();


    state.gallery.forEach(
      item => {

        URL.revokeObjectURL(
          item.url
        );
      }
    );
  }
);


/* ============================================================
   GLOBAL API
   ============================================================ */

window.triggerUpload =
  triggerUpload;

window.showEditor =
  showEditor;

window.showLanding =
  showLanding;

window.removeFromGallery =
  removeFromGallery;

window.startWebcam =
  startWebcam;

window.stopWebcam =
  stopWebcam;