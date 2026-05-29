interface ErrorBannerProps {
  message: string;
}

export default function ErrorBanner({ message }: ErrorBannerProps) {
  return (
    <section className="error-banner" role="alert" aria-live="assertive">
      <div className="error-banner-title">请求失败</div>
      <div className="error-banner-message">{message}</div>
    </section>
  );
}
