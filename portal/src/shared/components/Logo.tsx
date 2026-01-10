import { Link } from 'react-router-dom'

export function Logo() {
  return (
    <Link to="/" className="flex items-center gap-3 group">
      {/* Logo Icon - Design sofisticado com formas geométricas */}
      <div className="relative">
        <div className="absolute inset-0 bg-gradient-primary rounded-xl opacity-20 blur-md group-hover:opacity-30 transition-opacity"></div>
        <div className="relative p-2.5 bg-gradient-primary rounded-xl shadow-soft group-hover:shadow-glow transition-all duration-300">
          <svg
            width="24"
            height="24"
            viewBox="0 0 24 24"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
            className="text-white"
          >
            {/* Design sofisticado: Cubo 3D estilizado representando infraestrutura/plataforma */}
            <path
              d="M12 2L22 7L12 12L2 7L12 2Z"
              fill="currentColor"
              className="text-white/90"
            />
            <path
              d="M2 7L12 12V22L2 17V7Z"
              fill="currentColor"
              className="text-white/70"
            />
            <path
              d="M12 12L22 7V17L12 22V12Z"
              fill="currentColor"
              className="text-white/80"
            />
            {/* Linha decorativa */}
            <path
              d="M12 2L12 12M2 7L12 12M22 7L12 12"
              stroke="currentColor"
              strokeWidth="1.5"
              strokeLinecap="round"
              className="text-white/50"
            />
          </svg>
        </div>
      </div>
      {/* Texto do logo */}
      <div className="flex flex-col">
        <span className="text-xl font-bold text-gradient tracking-tight leading-tight">
          Tron
        </span>
        <span className="text-[10px] font-medium text-neutral-500 uppercase tracking-widest leading-none">
          Platform
        </span>
      </div>
    </Link>
  )
}

