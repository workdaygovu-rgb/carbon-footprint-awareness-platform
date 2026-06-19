interface NumberFieldProps {
  id: string;
  label: string;
  value: number;
  onChange: (value: number) => void;
  /** Upper bound, mirroring the backend schema so the browser rejects out-of-range values. */
  max: number;
  min?: number;
  step?: number | "any";
  /** Optional helper text, associated with the input via aria-describedby. */
  hint?: string;
}

/**
 * A labelled numeric input with consistent accessibility wiring: explicit
 * label association, optional hint exposed through `aria-describedby`, and
 * browser-level `min`/`max` bounds. Non-numeric input coerces to 0 so the
 * form state always holds a valid number.
 */
export function NumberField({
  id,
  label,
  value,
  onChange,
  max,
  min = 0,
  step = "any",
  hint,
}: NumberFieldProps) {
  const hintId = hint ? `${id}-hint` : undefined;
  return (
    <div className="field">
      <label htmlFor={id}>{label}</label>
      <input
        id={id}
        type="number"
        min={min}
        max={max}
        step={step}
        inputMode={step === "any" ? "decimal" : "numeric"}
        aria-describedby={hintId}
        value={value}
        onChange={(e) => {
          const next = Number(e.target.value);
          onChange(Number.isNaN(next) ? 0 : next);
        }}
      />
      {hint && (
        <span className="hint" id={hintId}>
          {hint}
        </span>
      )}
    </div>
  );
}
