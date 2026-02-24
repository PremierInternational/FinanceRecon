interface HeaderProps {
  title: string
}

export default function Header({ title }: HeaderProps) {
  return (
    <div className="app-header">
      <img src="/assets/modernization.svg" alt="logo" className="logo" />
      <img src="/assets/Trapz.svg" alt="" className="header-bg" aria-hidden="true" />
      <h1>{title}</h1>
    </div>
  )
}
