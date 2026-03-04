function ErrorState({ message, onRetry }) {
  return (
    <div className="error-state">
      <p>{message}</p>
      {onRetry ? (
        <button type="button" onClick={onRetry}>
          Retry
        </button>
      ) : null}
    </div>
  );
}

export default ErrorState;

