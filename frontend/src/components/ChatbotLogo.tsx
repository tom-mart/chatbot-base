'use client';

import Image from 'next/image';
import { useTheme } from '@/contexts/ThemeContext';

interface ChatbotLogoProps {
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl' | '2xl' | '3xl' | '4xl';
  variant?: 'default' | 'simple' | 'gradient';
  animated?: boolean;
  pulse?: boolean;
}

const sizeMap = {
  xs: 16,
  sm: 24,
  md: 32,
  lg: 40,
  xl: 48,
  '2xl': 64,
  '3xl': 80,
  '4xl': 96,
};

export default function ChatbotLogo({
  size = 'md',
  variant = 'default',
  animated = false,
  pulse = false,
}: ChatbotLogoProps) {
  const { theme } = useTheme();
  const pixelSize = sizeMap[size];
  
  // Determine which logo to use based on theme
  // Use white logo for dark themes, black for light themes
  const darkThemes = ['dark', 'night', 'dracula', 'synthwave', 'cyberpunk', 'halloween', 'forest', 'black', 'luxury', 'business'];
  const isDarkTheme = darkThemes.includes(theme);
  const logoSrc = isDarkTheme ? '/chatbot-white.PNG' : '/chatbot-black.PNG';

  return (
    <div className={`flex items-center justify-center ${animated ? 'animate-bounce' : ''} ${pulse ? 'animate-pulse' : ''}`}>
      <Image
        src={logoSrc}
        alt="Chatbot Logo"
        width={pixelSize}
        height={pixelSize}
        className="object-contain"
        priority
      />
    </div>
  );
}
