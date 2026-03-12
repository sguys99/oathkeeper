"use client";

import { useCallback } from "react";
import { useDropzone } from "react-dropzone";
import { cn } from "@/lib/utils";
import { FileUp, X } from "lucide-react";
import { Button } from "@/components/ui/button";

const MAX_SIZE = 20 * 1024 * 1024; // 20MB
const ACCEPTED = {
  "application/pdf": [".pdf"],
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [
    ".docx",
  ],
};

export function FileUploadZone({
  file,
  onFileChange,
  disabled,
}: {
  file: File | null;
  onFileChange: (file: File | null) => void;
  disabled?: boolean;
}) {
  const onDrop = useCallback(
    (accepted: File[]) => {
      if (accepted.length > 0) onFileChange(accepted[0]);
    },
    [onFileChange],
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: ACCEPTED,
    maxSize: MAX_SIZE,
    maxFiles: 1,
    disabled,
  });

  if (file) {
    return (
      <div className="flex items-center gap-2 rounded-md border px-3 py-2">
        <FileUp className="h-4 w-4 text-muted-foreground" />
        <span className="flex-1 truncate text-sm">{file.name}</span>
        <span className="text-xs text-muted-foreground">
          {(file.size / 1024 / 1024).toFixed(1)}MB
        </span>
        <Button
          variant="ghost"
          size="icon"
          className="h-6 w-6"
          onClick={() => onFileChange(null)}
          disabled={disabled}
        >
          <X className="h-3 w-3" />
        </Button>
      </div>
    );
  }

  return (
    <div
      {...getRootProps()}
      className={cn(
        "flex cursor-pointer flex-col items-center gap-2 rounded-md border-2 border-dashed px-4 py-6 text-center transition-colors",
        isDragActive
          ? "border-primary bg-primary/5"
          : "border-muted-foreground/25 hover:border-primary/50",
        disabled && "cursor-not-allowed opacity-50",
      )}
    >
      <input {...getInputProps()} />
      <FileUp className="h-8 w-8 text-muted-foreground" />
      <div className="text-sm text-muted-foreground">
        <span className="font-medium text-foreground">파일을 드래그</span>하거나{" "}
        <span className="font-medium text-foreground">클릭</span>하여 업로드
      </div>
      <p className="text-xs text-muted-foreground">
        .docx, .pdf (최대 20MB)
      </p>
    </div>
  );
}
