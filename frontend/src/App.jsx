import { useState, useRef, useEffect } from 'react';
import { checkApiHealth, generatePaintings } from './moodcanvas-api.js';
import { appendRecognizedText, getSpeechRecognitionConstructor } from './voice-input.js';
import './App.css';

const DADA_ROTATIONS = [-3, 2, -1, 3];
const DARKROOM_ROTATIONS = [2, -3, 1, -2, 3, -1, 2, -2];
const VOICE_WAVE_HEIGHTS = [12, 18, 28, 16, 36, 22, 30, 14, 34, 20, 26, 12, 24, 38, 18, 32, 14, 28, 20, 16];

export default function App() {
  const [uploadedImage, setUploadedImage] = useState(null);
  const [uploadedImageFile, setUploadedImageFile] = useState(null);
  const [userDescription, setUserDescription] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [generatedImages, setGeneratedImages] = useState([]);
  const [selectedImage, setSelectedImage] = useState(null);
  const [isGeneratingProduct, setIsGeneratingProduct] = useState(false);
  const [generatedProduct, setGeneratedProduct] = useState(null);
  const [showCamera, setShowCamera] = useState(false);
  const [cameraError, setCameraError] = useState(null);
  const [apiAvailable, setApiAvailable] = useState(null);
  const [isListening, setIsListening] = useState(false);
  const [voicePreview, setVoicePreview] = useState('');
  const [voiceError, setVoiceError] = useState(null);
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const streamRef = useRef(null);
  const recognitionRef = useRef(null);

  useEffect(() => {
    let active = true;

    checkApiHealth().then((available) => {
      if (active) {
        setApiAvailable(available);
      }
    });

    return () => {
      active = false;
    };
  }, []);

  const handleImageUpload = (e) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setUploadedImage(URL.createObjectURL(file));
      setUploadedImageFile(file);
      setGeneratedImages([]);
      setSelectedImage(null);
      setGeneratedProduct(null);
    }
  };

  // 打开摄像头
  const openCamera = async () => {
    try {
      setCameraError(null);
      // 先显示摄像头界面
      setShowCamera(true);
      
      // 等待下一轮渲染，确保video元素已经挂载
      await new Promise(resolve => setTimeout(resolve, 100));
      
      // 检查video元素是否存在
      if (!videoRef.current) {
        throw new Error('Video element not found');
      }
      
      const stream = await navigator.mediaDevices.getUserMedia({ 
        video: { 
          width: { ideal: 640 },
          height: { ideal: 480 },
          facingMode: 'environment' // 后置摄像头优先
        } 
      });
      
      streamRef.current = stream;
      videoRef.current.srcObject = stream;
      
      // 等待视频流稳定
      await new Promise(resolve => {
        if (videoRef.current.readyState >= 2) {
          resolve();
        } else {
          videoRef.current.onloadedmetadata = resolve;
        }
      });
      
    } catch (err) {
      console.error('摄像头访问失败:', err);
      setCameraError('无法访问摄像头，请检查权限设置或浏览器不支持');
      setShowCamera(false);
    }
  };

  // 拍照
  const capturePhoto = () => {
    if (videoRef.current && canvasRef.current) {
      const video = videoRef.current;
      const canvas = canvasRef.current;
      
      // 确保视频有有效尺寸
      if (video.videoWidth === 0 || video.videoHeight === 0) {
        setCameraError('视频流未准备好，请重试');
        return;
      }
      
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      const ctx = canvas.getContext('2d');
      ctx.drawImage(video, 0, 0);
      
      canvas.toBlob((blob) => {
        if (!blob) {
          setCameraError('照片生成失败，请重试');
          return;
        }

        closeCamera();
        setUploadedImage(URL.createObjectURL(blob));
        setUploadedImageFile(new File([blob], 'camera-capture.jpg', { type: 'image/jpeg' }));
        setGeneratedImages([]);
        setSelectedImage(null);
        setGeneratedProduct(null);
      }, 'image/jpeg', 0.9);
    } else {
      console.error('Video or canvas ref not available');
      setCameraError('摄像头出错，请重试');
    }
  };

  // 关闭摄像头
  const closeCamera = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }
    setShowCamera(false);
    setCameraError(null);
  };

  const startVoiceInput = () => {
    const SpeechRecognition = getSpeechRecognitionConstructor(window);

    if (!SpeechRecognition) {
      setVoiceError('您的浏览器不支持语音识别，请使用 Edge 或 Chrome。');
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = 'zh-CN';

    recognition.onstart = () => {
      setIsListening(true);
      setVoiceError(null);
      setVoicePreview('');
    };

    recognition.onresult = (event) => {
      let finalTranscript = '';
      let interimTranscript = '';

      for (let index = event.resultIndex; index < event.results.length; index += 1) {
        const transcript = event.results[index][0].transcript;
        if (event.results[index].isFinal) {
          finalTranscript += transcript;
        } else {
          interimTranscript += transcript;
        }
      }

      if (finalTranscript.trim()) {
        setUserDescription((current) => appendRecognizedText(current, finalTranscript));
        setVoicePreview('');
      } else {
        setVoicePreview(interimTranscript.trim());
      }
    };

    recognition.onerror = (event) => {
      const errorMessages = {
        'not-allowed': '麦克风权限被拒绝，请在浏览器中允许访问。',
        'no-speech': '没有识别到声音，请再说一次。',
        network: '语音识别网络连接失败，请重试。',
      };
      setVoiceError(errorMessages[event.error] || '语音识别失败，请重试。');
      setIsListening(false);
      recognitionRef.current = null;
    };

    recognition.onend = () => {
      setIsListening(false);
      setVoicePreview('');
      recognitionRef.current = null;
    };

    recognitionRef.current = recognition;
    recognition.start();
  };

  const stopVoiceInput = () => {
    recognitionRef.current?.stop();
  };

  const clearDescription = () => {
    setUserDescription('');
    setVoicePreview('');
    setVoiceError(null);
  };
  
  // 组件卸载时清理摄像头
  useEffect(() => {
    return () => {
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
      }
      recognitionRef.current?.stop();
    };
  }, []);

  const handleGenerate = async () => {
    if (!uploadedImageFile || !userDescription.trim()) {
      alert('请先上传或拍摄图片，并描述你的感受。');
      return;
    }

    setIsGenerating(true);
    setSelectedImage(null);
    setGeneratedProduct(null);
    
    try {
      const paintings = await generatePaintings(uploadedImageFile, userDescription);
      setGeneratedImages(paintings);
    } catch (error) {
      console.error('生成图片失败:', error);
      alert(error.message || '生成图片失败，请重试。');
    } finally {
      setIsGenerating(false);
    }
  };

  // API接口：根据选中的图片生成创意产品
  const handleSelectImage = async (imgUrl) => {
    setSelectedImage(imgUrl);
    setIsGeneratingProduct(true);
    setGeneratedProduct(null);

    try {
      // TODO: 后端对接 - 调用真实API生成创意产品
      // const response = await fetch(`${API_BASE_URL}/generate-product`, {
      //   method: 'POST',
      //   headers: { 'Content-Type': 'application/json' },
      //   body: JSON.stringify({
      //     selectedImage: imgUrl,
      //     description: userDescription
      //   })
      // });
      // const data = await response.json();
      // setGeneratedProduct(data.product);

      // 模拟API调用 - 后端对接时删除这段代码
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      // 模拟AI生成的创意产品数据
      const mockProducts = [
        {
          type: '解构主义帆布袋',
          description: '提取了图片中的几何碎片元素，创造出充满张力的视觉冲击',
          previewImage: imgUrl,
          elements: ['几何碎片', '错位构图', '荒诞色彩']
        },
        {
          type: '达达主义手机壳',
          description: '将图片中的荒诞元素重组，形成独特的后现代艺术风格',
          previewImage: imgUrl,
          elements: ['拼贴艺术', '反逻辑构图', '霓虹色彩']
        },
        {
          type: '超现实主义艺术徽章',
          description: '捕捉图片中的超现实意象，打造独一无二的个性徽章',
          previewImage: imgUrl,
          elements: ['梦境意象', '扭曲形态', '象征符号']
        }
      ];
      
      const productIndex = imgUrl.length % mockProducts.length;
      setGeneratedProduct(mockProducts[productIndex]);
      
    } catch (error) {
      console.error('生成产品失败:', error);
      alert('生成产品失败，请重试');
    } finally {
      setIsGeneratingProduct(false);
    }
  };

  return (
    <div className="min-h-screen w-full relative bg-[#f4ebe0] overflow-x-hidden font-sans">
      
      {/* 底层：做旧纸张纹理 */}
      <div 
        className="fixed inset-0 z-0 pointer-events-none"
        style={{
          backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.8' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)'/%3E%3C/svg%3E")`,
          opacity: 0.08,
          backgroundColor: '#f4ebe0'
        }}
      ></div>

      {/* 拼贴碎片装饰 - 荒诞派元素 */}
      <div className="fixed inset-0 z-0 pointer-events-none overflow-hidden">
        
        {/* 大型几何碎片层 - 左上区域 */}
        <div className="absolute top-[5%] left-[2%] w-40 h-32 bg-[#2d2d2d] transform rotate-15 opacity-40"></div>
        <div className="absolute top-[12%] left-[15%] w-28 h-20 bg-[#d9a05b] transform -rotate-8 opacity-35"></div>
        <div className="absolute top-[8%] left-[30%] w-24 h-24 bg-[#cf0] transform rotate-45 opacity-30"></div>
        <div className="absolute top-[20%] left-[8%] w-32 h-16 bg-[#ff6b6b] transform rotate-30 opacity-35"></div>
        
        {/* 大型几何碎片层 - 右上区域 */}
        <div className="absolute top-[10%] right-[5%] w-36 h-28 bg-[#d9a05b] transform -rotate-12 opacity-40"></div>
        <div className="absolute top-[5%] right-[20%] w-24 h-24 bg-[#2d2d2d] transform rotate-20 opacity-30"></div>
        <div className="absolute top-[18%] right-[15%] w-20 h-32 bg-[#cf0] transform -rotate-45 opacity-35"></div>
        <div className="absolute top-[25%] right-[8%] w-28 h-20 bg-[#ff6b6b] transform rotate-8 opacity-30"></div>
        
        {/* 大型几何碎片层 - 左下区域 */}
        <div className="absolute bottom-[10%] left-[3%] w-36 h-24 bg-[#ff6b6b] transform -rotate-18 opacity-40"></div>
        <div className="absolute bottom-[20%] left-[12%] w-24 h-28 bg-[#2d2d2d] transform rotate-12 opacity-35"></div>
        <div className="absolute bottom-[8%] left-[25%] w-28 h-20 bg-[#d9a05b] transform -rotate-25 opacity-30"></div>
        <div className="absolute bottom-[25%] left-[6%] w-20 h-24 bg-[#cf0] transform rotate-35 opacity-35"></div>
        
        {/* 大型几何碎片层 - 右下区域 */}
        <div className="absolute bottom-[12%] right-[4%] w-32 h-28 bg-[#2d2d2d] transform rotate-22 opacity-40"></div>
        <div className="absolute bottom-[5%] right-[18%] w-24 h-24 bg-[#ff6b6b] transform -rotate-15 opacity-35"></div>
        <div className="absolute bottom-[22%] right-[10%] w-28 h-20 bg-[#d9a05b] transform rotate-28 opacity-30"></div>
        
        {/* 圆形装饰层 */}
        <div className="absolute top-[25%] left-[5%] w-20 h-20 border-6 border-[#2d2d2d] rounded-full opacity-45"></div>
        <div className="absolute top-[35%] left-[12%] w-16 h-16 bg-[#d9a05b] rounded-full opacity-35"></div>
        <div className="absolute bottom-[35%] left-[8%] w-24 h-24 border-4 border-[#ff6b6b] rounded-full opacity-40"></div>
        
        <div className="absolute top-[30%] right-[6%] w-20 h-20 border-6 border-[#d9a05b] rounded-full opacity-45"></div>
        <div className="absolute top-[22%] right-[15%] w-16 h-16 bg-[#2d2d2d] rounded-full opacity-35"></div>
        <div className="absolute bottom-[30%] right-[8%] w-28 h-28 border-4 border-[#cf0] rounded-full opacity-40"></div>
        
        {/* 三角形装饰层 */}
        <div className="absolute top-[40%] left-[10%] w-0 h-0 opacity-45" style={{ borderLeft: '35px solid transparent', borderRight: '35px solid transparent', borderBottom: '60px solid #ff6b6b', transform: 'rotate(20deg)' }}></div>
        <div className="absolute top-[15%] left-[22%] w-0 h-0 opacity-35" style={{ borderLeft: '30px solid transparent', borderRight: '30px solid transparent', borderBottom: '50px solid #2d2d2d', transform: 'rotate(-15deg)' }}></div>
        <div className="absolute bottom-[45%] left-[5%] w-0 h-0 opacity-40" style={{ borderLeft: '40px solid transparent', borderRight: '40px solid transparent', borderBottom: '70px solid #d9a05b', transform: 'rotate(35deg)' }}></div>
        
        <div className="absolute top-[50%] right-[12%] w-0 h-0 opacity-45" style={{ borderLeft: '35px solid transparent', borderRight: '35px solid transparent', borderBottom: '60px solid #2d2d2d', transform: 'rotate(-25deg)' }}></div>
        <div className="absolute top-[35%] right-[20%] w-0 h-0 opacity-35" style={{ borderLeft: '30px solid transparent', borderRight: '30px solid transparent', borderBottom: '50px solid #cf0', transform: 'rotate(18deg)' }}></div>
        
        {/* 复杂螺旋图案 SVG */}
        <svg className="absolute top-[50%] right-[3%] w-40 h-40 opacity-30" viewBox="0 0 100 100">
          <path d="M50 10 Q60 10 60 20 Q60 30 50 30 Q40 30 40 20 Q40 15 45 15 Q55 15 55 25 Q55 35 45 35 Q35 35 35 25 Q35 20 40 20 Q50 20 50 30 Q50 40 40 40 Q30 40 30 30 Q30 25 35 25 Q45 25 45 35 Q45 45 35 45 Q25 45 25 35 Q25 30 30 30 Q40 30 40 40 Q40 50 30 50 Q20 50 20 40 Q20 35 25 35 Q35 35 35 45 Q35 55 25 55 Q15 55 15 45 Q15 40 20 40 Q30 40 30 50 Q30 60 20 60 Q10 60 10 50 Q10 45 15 45 Q25 45 25 55 Q25 65 15 65 Q5 65 5 55 Q5 50 10 50 Q20 50 20 60 Q20 70 10 70" fill="none" stroke="#2d2d2d" strokeWidth="3"/>
        </svg>
        
        <svg className="absolute bottom-[15%] left-[2%] w-32 h-32 opacity-25" viewBox="0 0 100 100">
          <path d="M20 50 Q20 20 50 20 Q80 20 80 50 Q80 80 50 80 Q20 80 20 50" fill="none" stroke="#d9a05b" strokeWidth="2"/>
          <path d="M30 50 Q30 30 50 30 Q70 30 70 50 Q70 70 50 70 Q30 70 30 50" fill="none" stroke="#ff6b6b" strokeWidth="2"/>
          <path d="M40 50 Q40 40 50 40 Q60 40 60 50 Q60 60 50 60 Q40 60 40 50" fill="none" stroke="#cf0" strokeWidth="2"/>
        </svg>
        
        {/* 达达主义风格文字碎片 - 多层 */}
        <div className="absolute top-[8%] right-[30%] text-lg font-black text-[#d9a05b] opacity-55 transform rotate-12 tracking-widest">NONSENSE</div>
        <div className="absolute top-[12%] right-[35%] text-sm font-black text-[#2d2d2d] opacity-45 transform rotate-8">DADA</div>
        
        <div className="absolute bottom-[35%] left-[3%] text-base font-black text-[#2d2d2d] opacity-50 transform -rotate-8">IRRATIONAL</div>
        <div className="absolute bottom-[40%] left-[8%] text-sm font-black text-[#ff6b6b] opacity-40 transform -rotate-5">ABSURD</div>
        
        <div className="absolute top-[65%] right-[20%] text-base font-black text-[#ff6b6b] opacity-50 transform rotate-45">???</div>
        <div className="absolute top-[70%] right-[25%] text-sm font-black text-[#cf0] opacity-45 transform rotate-50">!!!</div>
        
        <div className="absolute top-[80%] left-[35%] text-base font-black text-[#cf0] opacity-50">DADA</div>
        <div className="absolute top-[85%] left-[40%] text-sm font-black text-[#d9a05b] opacity-45 transform rotate-5">ART</div>
        
        {/* 数学公式和符号装饰层 */}
        <div className="absolute top-[30%] left-[3%] text-base text-[#666] opacity-45 font-serif">
          <p className="transform -rotate-6">x + 1 = 0</p>
          <p className="transform rotate-3">π ≈ 3.14</p>
          <p className="transform -rotate-3">∅ ∈ R</p>
        </div>
        
        <div className="absolute bottom-[25%] right-[3%] text-base text-[#666] opacity-45 font-serif">
          <p className="transform rotate-8">∞ + 1 = ∞</p>
          <p className="transform -rotate-5">√-1 = i</p>
        </div>
        
        {/* 撕裂纸张边缘和线条效果 */}
        <div className="absolute top-[55%] left-[10%] w-48 h-2 bg-[#2d2d2d] opacity-35 transform rotate-45"></div>
        <div className="absolute top-[58%] left-[12%] w-32 h-1 bg-[#d9a05b] opacity-40 transform rotate-40"></div>
        <div className="absolute top-[75%] right-[8%] w-40 h-2 bg-[#ff6b6b] opacity-35 transform -rotate-30"></div>
        <div className="absolute top-[78%] right-[12%] w-28 h-1 bg-[#2d2d2d] opacity-40 transform -rotate-25"></div>
        
        {/* 不规则拼贴碎片 */}
        <div className="absolute top-[45%] left-[8%] opacity-35" style={{ width: '70px', height: '50px', backgroundColor: '#2d2d2d', clipPath: 'polygon(0 0, 100% 10%, 90% 100%, 10% 90%)' }}></div>
        <div className="absolute bottom-[15%] right-[28%] opacity-40" style={{ width: '60px', height: '60px', backgroundColor: '#cf0', clipPath: 'polygon(50% 0%, 100% 50%, 50% 100%, 0% 50%)' }}></div>
        <div className="absolute top-[60%] left-[15%] opacity-35" style={{ width: '50px', height: '70px', backgroundColor: '#d9a05b', clipPath: 'polygon(20% 0%, 100% 0%, 80% 100%, 0% 100%)' }}></div>
        
        {/* 网格线装饰 */}
        <div className="absolute top-[70%] left-[22%] w-28 h-28 border border-[#2d2d2d]/35 opacity-50" style={{ backgroundImage: 'linear-gradient(#2d2d2d 1px, transparent 1px), linear-gradient(90deg, #2d2d2d 1px, transparent 1px)', backgroundSize: '12px 12px' }}></div>
        
        <div className="absolute bottom-[50%] right-[18%] w-24 h-24 border border-[#d9a05b]/35 opacity-45" style={{ backgroundImage: 'linear-gradient(#d9a05b 1px, transparent 1px), linear-gradient(90deg, #d9a05b 1px, transparent 1px)', backgroundSize: '10px 10px' }}></div>
        
        {/* 大型数字和符号装饰 */}
        <div className="absolute top-[15%] left-[65%] text-4xl font-black text-[#ff6b6b] opacity-40 transform -rotate-12">3.14</div>
        <div className="absolute bottom-[8%] left-[18%] text-3xl font-black text-[#2d2d2d] opacity-45 transform rotate-8">∞</div>
        <div className="absolute top-[88%] right-[45%] text-3xl font-black text-[#d9a05b] opacity-40 transform -rotate-6">!</div>
        <div className="absolute top-[18%] right-[42%] text-2xl font-black text-[#cf0] opacity-35 transform rotate-15">%</div>
        <div className="absolute bottom-[18%] left-[45%] text-2xl font-black text-[#ff6b6b] opacity-40 transform -rotate-10">@</div>
        
        {/* 小方块阵列 - 左上 */}
        {Array.from({ length: 12 }).map((_, i) => (
          <div 
            key={`block-left-${i}`}
            className="absolute bg-[#2d2d2d] opacity-30"
            style={{
              width: '14px',
              height: '14px',
              top: `${40 + (i % 4) * 5}%`,
              left: `${92 + Math.floor(i / 4) * 3}%`,
              transform: `rotate(${i * 12}deg)`
            }}
          ></div>
        ))}
        
        {/* 小方块阵列 - 右下 */}
        {Array.from({ length: 9 }).map((_, i) => (
          <div 
            key={`block-right-${i}`}
            className="absolute bg-[#d9a05b] opacity-30"
            style={{
              width: '12px',
              height: '12px',
              top: `${70 + (i % 3) * 4}%`,
              left: `${88 + Math.floor(i / 3) * 3}%`,
              transform: `rotate(${i * 15}deg)`
            }}
          ></div>
        ))}
        
        {/* 额外的拼贴艺术元素 - 箭头和符号 */}
        <div className="absolute top-[72%] left-[5%] w-0 h-0 opacity-40" style={{ borderLeft: '20px solid #ff6b6b', borderTop: '10px solid transparent', borderBottom: '10px solid transparent' }}></div>
        <div className="absolute bottom-[55%] right-[5%] w-0 h-0 opacity-40" style={{ borderRight: '20px solid #2d2d2d', borderTop: '10px solid transparent', borderBottom: '10px solid transparent' }}></div>
        
        {/* 菱形装饰 */}
        <div className="absolute top-[80%] right-[12%] w-20 h-20 border-6 border-[#ff6b6b] opacity-35" style={{ clipPath: 'polygon(50% 0%, 100% 50%, 50% 100%, 0% 50%)' }}></div>
        <div className="absolute top-[20%] left-[48%] w-16 h-16 border-4 border-[#cf0] opacity-35" style={{ clipPath: 'polygon(50% 0%, 100% 50%, 50% 100%, 0% 50%)' }}></div>
        
        {/* 虚线装饰 */}
        <div className="absolute top-[62%] left-[6%] border-t-4 border-dashed border-[#2d2d2d] opacity-35" style={{ width: '80px', transform: 'rotate(-15deg)' }}></div>
        <div className="absolute bottom-[38%] right-[10%] border-t-4 border-dashed border-[#d9a05b] opacity-40" style={{ width: '60px', transform: 'rotate(25deg)' }}></div>
        
        {/* 额外的艺术文字 */}
        <div className="absolute top-[25%] left-[50%] text-xs font-black text-[#2d2d2d] opacity-35 transform -rotate-45 tracking-widest">CHAOS</div>
        <div className="absolute bottom-[32%] left-[50%] text-xs font-black text-[#ff6b6b] opacity-40 transform rotate-30">CRAZY</div>
        <div className="absolute top-[88%] left-[50%] text-xs font-black text-[#d9a05b] opacity-35 transform -rotate-15">MODERN</div>
        
        {/* 小圆点装饰群 */}
        {Array.from({ length: 6 }).map((_, i) => (
          <div 
            key={`dot-${i}`}
            className="absolute bg-[#ff6b6b] rounded-full opacity-30"
            style={{
              width: '8px',
              height: '8px',
              top: `${28 + i * 10}%`,
              left: `${2 + i * 1.5}%`,
            }}
          ></div>
        ))}
        
        {Array.from({ length: 5 }).map((_, i) => (
          <div 
            key={`dot2-${i}`}
            className="absolute bg-[#cf0] rounded-full opacity-30"
            style={{
              width: '10px',
              height: '10px',
              bottom: `${15 + i * 12}%`,
              right: `${3 + i * 2}%`,
            }}
          ></div>
        ))}
      </div>

      {/* 高层：交互主容器 */}
      <div className="relative z-10 w-full min-h-screen flex flex-col items-center justify-center p-4 py-12">
        
        {/* 标题区：拼贴艺术风格 - 大幅放大 */}
        <div className="flex justify-center w-full mb-12">
          <div className="flex flex-wrap justify-center items-end gap-1">
            {['D', 'A', 'D', 'A'].map((letter, i) => (
              <span 
                key={i}
                className={`font-black tracking-tighter letter-shake letter-shake-${i + 1}`}
                style={{
                  fontSize: '4rem',
                  color: i === 0 || i === 2 ? '#2d2d2d' : '#fff',
                  backgroundColor: i === 1 ? '#2d2d2d' : i === 3 ? '#2d2d2d' : 'transparent',
                  padding: i % 2 === 1 ? '8px 12px' : '0',
                  transform: `rotate(${DADA_ROTATIONS[i]}deg)`,
                  boxShadow: i % 2 === 1 ? '4px 4px 0px 0px rgba(0,0,0,0.3)' : 'none'
                }}
              >
                {letter}
              </span>
            ))}
            <span className="mx-4"></span>
            {['D', 'A', 'R', 'K', 'R', 'O', 'O', 'M'].map((letter, i) => {
              const colors = ['#2d2d2d', '#cf0', '#2d2d2d', '#ff6b6b', '#2d2d2d', '#2d2d2d', '#ff6b6b', '#2d2d2d'];
              return (
                <span 
                  key={i}
                  className={`font-black tracking-tighter letter-shake letter-shake-${i + 5}`}
                  style={{
                    fontSize: '4rem',
                    color: i === 1 || i === 3 || i === 6 ? '#2d2d2d' : '#fff',
                    backgroundColor: colors[i],
                    padding: '8px 12px',
                    transform: `rotate(${DARKROOM_ROTATIONS[i]}deg)`,
                    boxShadow: '4px 4px 0px 0px rgba(0,0,0,0.3)'
                  }}
                >
                  {letter}
                </span>
              );
            })}
          </div>
        </div>

        {/* 副标题 */}
        <div className="mb-12 text-center">
          <div 
            className="inline-block bg-[#2d2d2d] text-[#f4ebe0] font-bold px-6 py-2 text-lg transform -rotate-2"
            style={{ boxShadow: '4px 4px 0px 0px rgba(0,0,0,0.3)' }}
          >
            达达暗房 | DADA DARKROOM
          </div>
        </div>

        {/* 核心中控面板 */}
        <div 
          className="w-full max-w-2xl bg-[#f4ebe0]/95 flex flex-col relative" 
          style={{ 
            boxShadow: '8px 8px 0px 0px rgba(0,0,0,1)',
            border: '4px solid #2d2d2d'
          }}
        >
          {/* 右上角装饰文字 */}
          <div className="absolute -top-6 -right-6 text-xs font-bold text-[#d9a05b] transform rotate-12 opacity-60">
            MODERN ART
          </div>

          {/* 区域 A：输入设备窗口 */}
          <div className="w-full grid grid-cols-1 md:grid-cols-2 gap-6 p-7 pb-0 relative z-10">
            <div className="relative window-shake">
              <div className="bg-[#4ecdc4] border-x-4 border-t-4 border-[#2d2d2d] px-3 py-2 flex items-center justify-between">
                <span className="text-[10px] font-black tracking-widest">PHOTO_UPLOAD.WIN</span>
                <span className="text-xs font-black">[_][X]</span>
              </div>
              <label className="min-h-[150px] bg-white border-4 border-[#2d2d2d] flex flex-col items-center justify-center cursor-pointer hover:bg-[#fff7db] transition-colors">
                <span className="text-sm font-black tracking-[0.2em] slow-pulse">[ UPLOAD ]</span>
                <p className="text-[10px] font-bold text-[#666] mt-3">DROP YOUR REALITY HERE</p>
                <input type="file" className="hidden" accept="image/*" onChange={handleImageUpload} />
              </label>
            </div>
            <div className="relative window-shake">
              <div className="bg-[#ff9f43] border-x-4 border-t-4 border-[#2d2d2d] px-3 py-2 flex items-center justify-between">
                <span className="text-[10px] font-black tracking-widest">CAMERA_APP.EXE</span>
                <span className="text-xs font-black">REC</span>
              </div>
              <button type="button" onClick={openCamera} className="w-full min-h-[150px] bg-[#f4ebe0] border-4 border-[#2d2d2d] flex flex-col items-center justify-center hover:bg-[#fff7db] transition-colors">
                <span className="text-sm font-black tracking-[0.2em] slow-pulse">[ CAPTURE ]</span>
                <span className="text-[10px] font-bold text-[#666] mt-3">CLICK TO SNAP</span>
              </button>
            </div>
            {showCamera && (
              <div className="md:col-span-2 relative bg-[#2d2d2d] border-4 border-[#2d2d2d]" style={{ boxShadow: '8px 8px 0px 0px rgba(0,0,0,0.3)' }}>
                <div className="bg-[#cf0] text-[#2d2d2d] px-4 py-2 text-xs font-black tracking-widest">LIVE_CAMERA.FEED</div>
                <video ref={videoRef} autoPlay playsInline muted className="w-full max-h-[400px] object-cover" />
                <canvas ref={canvasRef} className="hidden" />
                <div className="flex justify-center gap-4 p-4">
                  <button type="button" onClick={capturePhoto} className="px-8 py-3 bg-[#cf0] font-black border-4 border-[#2d2d2d]">SNAP</button>
                  <button type="button" onClick={closeCamera} className="px-8 py-3 bg-[#ff6b6b] font-black border-4 border-[#2d2d2d]">CANCEL</button>
                </div>
                {cameraError && <div className="absolute top-12 left-2 bg-[#ff6b6b] px-4 py-2 font-bold text-sm border-2 border-[#2d2d2d]">{cameraError}</div>}
              </div>
            )}
            {uploadedImage && !showCamera && (
              <div className="md:col-span-2 relative bg-white border-4 border-[#2d2d2d] p-4 flex items-center gap-5">
                <div className="absolute -top-4 left-4 bg-[#cf0] border-2 border-[#2d2d2d] px-3 py-1 text-[10px] font-black">IMAGE.PREVIEW</div>
                <img src={uploadedImage} alt="Preview" className="mt-2 w-[112px] h-[112px] object-cover border-4 border-[#2d2d2d]" style={{ boxShadow: '5px 5px 0px 0px rgba(0,0,0,0.25)' }} />
                <p className="text-xs font-black tracking-widest">REALITY LOADED // READY</p>
                <button type="button" onClick={() => {
                  setUploadedImage(null);
                  setUploadedImageFile(null);
                  setGeneratedImages([]);
                  setSelectedImage(null);
                  setGeneratedProduct(null);
                }} className="ml-auto w-9 h-9 bg-[#ff6b6b] font-black border-2 border-[#2d2d2d]">X</button>
              </div>
            )}
          </div>

          {/* 区域 B：语音与文本输入窗口 */}
          <div className="w-full grid grid-cols-1 md:grid-cols-2 gap-6 p-7 pt-7 pb-0 relative z-10">
            <div className="relative">
              <div className="bg-[#ff9f43] border-x-4 border-t-4 border-[#2d2d2d] px-3 py-2 flex items-center justify-between">
                <span className="text-[10px] font-black tracking-widest">VOICE_INPUT.APP</span>
                <div className="flex gap-1"><span className="w-2 h-2 bg-[#4ecdc4] border border-[#2d2d2d]"></span><span className="w-2 h-2 bg-[#cf0] border border-[#2d2d2d]"></span></div>
              </div>
              <div className="min-h-[245px] bg-[#f4ebe0] border-4 border-[#2d2d2d] p-4 flex flex-col justify-between">
                <div>
                  {isListening && (
                    <div className="h-11 flex items-end justify-center gap-0.5 mb-3">
                      {VOICE_WAVE_HEIGHTS.map((height, index) => (
                        <div key={height + index} className="w-1.5 voice-wave" style={{ backgroundColor: ['#ff6b6b', '#4ecdc4', '#d9a05b', '#cf0'][index % 4], height: `${height}px`, animationDelay: `${index * 0.02}s` }} />
                      ))}
                    </div>
                  )}
                  <p className="text-center text-xs font-black tracking-wider mb-3">{isListening ? 'LISTENING...' : 'READY FOR INPUT'}</p>
                  {(voicePreview || isListening) && <div className="p-2 bg-white border-2 border-[#2d2d2d] text-xs font-bold mb-3">{voicePreview || '...'}</div>}
                  {voiceError && <p className="text-xs font-bold text-[#d94841] mb-3">{voiceError}</p>}
                </div>
                <div className="flex gap-3 justify-center">
                  <button type="button" onClick={isListening ? stopVoiceInput : startVoiceInput} className={`px-5 py-3 border-4 border-[#2d2d2d] font-black text-xs ${isListening ? 'bg-[#ff6b6b]' : 'bg-[#4ecdc4]'}`}>{isListening ? 'STOP' : 'SPEAK'}</button>
                  {userDescription && <button type="button" onClick={clearDescription} className="px-4 py-3 bg-[#2d2d2d] text-white font-black text-xs">CLEAR</button>}
                </div>
              </div>
            </div>
            <div className="relative">
              <div className="bg-[#a29bfe] border-x-4 border-t-4 border-[#2d2d2d] px-3 py-2 flex items-center justify-between">
                <span className="text-[10px] font-black tracking-widest">TEXT_INPUT.TXT</span>
                <span className="text-xs font-black">_</span>
              </div>
              <textarea className="w-full min-h-[245px] bg-white border-4 border-[#2d2d2d] p-4 text-sm focus:outline-none focus:bg-[#fff7db] resize-none font-bold" placeholder="TYPE YOUR ABSURD FEELING HERE..." value={userDescription} onChange={(event) => setUserDescription(event.target.value)} />
              <span className="absolute -bottom-4 right-3 text-[10px] font-black text-[#d9a05b]">TYPE // SPEAK</span>
            </div>
          </div>

          {/* 区域 C：按钮 - 大幅增大 */}
          <div className="flex flex-col items-center w-full mt-12 mb-12 px-8 gap-5">
            <div
              className="px-5 py-2 border-2 border-[#2d2d2d] font-black text-xs tracking-[0.22em] transform -rotate-1"
              style={{
                backgroundColor: apiAvailable ? '#cf0' : '#2d2d2d',
                color: apiAvailable ? '#2d2d2d' : '#f4ebe0',
                boxShadow: '4px 4px 0px 0px rgba(0,0,0,0.25)',
              }}
            >
              {apiAvailable === null && 'MOODCANVAS // CONNECTING'}
              {apiAvailable === true && 'MOODCANVAS API CONNECTED // 5 PAINTINGS'}
              {apiAvailable === false && 'MOODCANVAS API OFFLINE // START BACKEND'}
            </div>
            <button 
              onClick={handleGenerate}
              disabled={isGenerating || !uploadedImageFile || !userDescription.trim()}
              className="relative px-28 py-8 bg-[#d9a05b] text-[#2d2d2d] font-black shadow-[10px_10px_0px_0px_rgba(0,0,0,1)] hover:translate-x-[2px] hover:translate-y-[2px] hover:shadow-[8px_8px_0px_0px_rgba(0,0,0,1)] active:shadow-none active:translate-x-[10px] active:translate-y-[10px] transition-all disabled:opacity-50 disabled:cursor-not-allowed border-4 border-[#2d2d2d] flex items-center justify-center gap-2 overflow-hidden"
              style={{ fontSize: '2rem' }}
            >
              <span className="z-10 tracking-wider">
                {isGenerating ? 'PROCESSING...' : '解构现实'}
              </span>
            </button>
          </div>

      {/* 区域 D：生成的图像网格 */}
          {generatedImages.length > 0 && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 px-8 pb-8">
              {generatedImages.map((painting, idx) => (
                <div key={`${painting.imageUrl}-${idx}`} className={`relative group ${idx === 0 ? 'md:col-span-2' : ''}`}>
                  <img 
                    src={painting.imageUrl} 
                    onClick={() => handleSelectImage(painting.imageUrl)}
                    className={`${idx === 0 ? 'aspect-[16/10]' : 'aspect-square'} w-full object-cover cursor-pointer transition-all duration-300 ${selectedImage === painting.imageUrl ? 'ring-4 ring-[#d9a05b] scale-105' : ''}`}
                    alt={painting.title || `Generated ${idx + 1}`}
                    style={{ 
                      border: '3px solid #2d2d2d',
                      boxShadow: selectedImage === painting.imageUrl ? '6px 6px 0px 0px rgba(0,0,0,0.3)' : '4px 4px 0px 0px rgba(0,0,0,0.2)',
                      transform: `rotate(${idx % 2 === 0 ? -1 : 1}deg)`,
                      filter: 'grayscale(100%)',
                    }}
                    onMouseEnter={(e) => { e.target.style.filter = 'grayscale(0%)'; }}
                    onMouseLeave={(e) => { e.target.style.filter = 'grayscale(100%)'; }}
                  />
                  <div className="absolute left-3 bottom-3 bg-[#2d2d2d] text-[#f4ebe0] text-xs font-bold px-3 py-1 max-w-[80%] truncate">
                    {painting.title}
                  </div>
                  {selectedImage === painting.imageUrl && (
                     <div className="absolute -bottom-2 -right-2 bg-[#cf0] text-[#2d2d2d] text-xs font-black px-2 py-1 border-2 border-[#2d2d2d] transform rotate-6" style={{ boxShadow: '2px 2px 0px 0px rgba(0,0,0,0.3)' }}>
                        SELECTED
                     </div>
                  )}
                </div>
              ))}
            </div>
          )}

        </div>

        {/* 区域 E：AI生成的创意产品 */}
        {selectedImage && (
           <div 
              className="w-full max-w-xl mt-12 bg-[#f4ebe0] p-6 border-4 border-[#2d2d2d] text-center relative"
              style={{ boxShadow: '8px 8px 0px 0px rgba(0,0,0,1)' }}
           >
              <h3 className="text-[#2d2d2d] font-black mb-6 tracking-widest text-sm uppercase" style={{ textDecoration: 'underline' }}>
                AI创意工坊 | AI CREATIVE LAB
              </h3>
              
              {isGeneratingProduct ? (
                <div className="flex flex-col items-center justify-center py-8">
                  <div className="w-12 h-12 border-4 border-[#d9a05b] border-t-transparent rounded-full animate-spin mb-4"></div>
                  <p className="text-[#2d2d2d] font-bold">AI正在解构你的选择...</p>
                </div>
              ) : generatedProduct ? (
                <div className="flex flex-col items-center gap-6">
                  {/* 产品预览图 */}
                  <div className="relative">
                    <img 
                      src={generatedProduct.previewImage} 
                      className="w-40 h-40 object-cover border-4 border-[#2d2d2d]"
                      style={{ 
                        borderRadius: '12px',
                        boxShadow: '6px 6px 0px 0px rgba(0,0,0,0.3)'
                      }}
                      alt="Generated Product"
                    />
                    <div 
                      className="absolute -top-3 -right-3 bg-[#cf0] text-[#2d2d2d] text-xs font-black px-3 py-1 border-2 border-[#2d2d2d] transform rotate-6"
                      style={{ boxShadow: '2px 2px 0px 0px rgba(0,0,0,0.3)' }}
                    >
                      AI生成
                    </div>
                  </div>
                  
                  {/* 产品信息 */}
                  <div className="text-left w-full px-4">
                    <h4 className="text-lg font-black text-[#2d2d2d] mb-2">{generatedProduct.type}</h4>
                    <p className="text-sm text-[#666] mb-4">{generatedProduct.description}</p>
                    
                    {/* 提取的元素标签 */}
                    <div className="flex flex-wrap gap-2">
                      {generatedProduct.elements.map((element, i) => (
                        <span 
                          key={i}
                          className="text-xs font-bold px-3 py-1 border-2 border-[#2d2d2d]"
                          style={{ 
                            backgroundColor: ['#d9a05b', '#cf0', '#ff6b6b'][i % 3],
                            boxShadow: '2px 2px 0px 0px rgba(0,0,0,0.2)'
                          }}
                        >
                          {element}
                        </span>
                      ))}
                    </div>
                  </div>
                  
                  {/* 重新生成按钮 */}
                  <button
                    onClick={() => handleSelectImage(selectedImage)}
                    className="px-6 py-2 bg-[#2d2d2d] text-[#f4ebe0] font-bold border-2 border-[#2d2d2d] hover:bg-[#d9a05b] hover:text-[#2d2d2d] transition-colors"
                    style={{ boxShadow: '4px 4px 0px 0px rgba(0,0,0,0.3)' }}
                  >
                    重新生成
                  </button>
                </div>
              ) : null}
           </div>
        )}

        {/* 底部装饰文字 */}
        <div className="mt-12 text-center">
          <p className="text-xs text-[#666] font-bold tracking-widest">DECONSTRUCT REALITY, RESHAPE EMOTION</p>
        </div>

      </div>
    </div>
  );
}
