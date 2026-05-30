interface ErrorBannerProps {
  message: string;
}

export default function ErrorBanner({ message }: ErrorBannerProps) {
  return (
    <section className="error-banner motion-enter motion-delay-2" role="alert" aria-live="assertive">
      <div className="error-banner-icon" aria-hidden="true">
        !
      </div>
      <div>
        <div className="error-banner-title">Request failed</div>
        <div className="error-banner-message">{message}</div>
      </div>
    </section>
  );
}
