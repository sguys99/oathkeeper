"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  useCostItems,
  useCreateCostItem,
  useUpdateCostItem,
  useDeleteCostItem,
  useSaveCostItemsDefaults,
} from "@/hooks/use-settings";
import { toast } from "sonner";
import { Plus, Pencil, Trash2, Loader2 } from "lucide-react";
import { formatCurrency } from "@/lib/utils";
import type { CostItemCreate, CostItemResponse } from "@/lib/api/types";

function CostItemFormDialog({
  open,
  onOpenChange,
  item,
  onSubmit,
  isPending,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  item: CostItemResponse | null;
  onSubmit: (data: CostItemCreate) => void;
  isPending: boolean;
}) {
  const [name, setName] = useState(item?.name ?? "");
  const [amount, setAmount] = useState(item?.amount?.toString() ?? "");
  const [description, setDescription] = useState(item?.description ?? "");

  useEffect(() => {
    setName(item?.name ?? "");
    setAmount(item?.amount?.toString() ?? "");
    setDescription(item?.description ?? "");
  }, [item]);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{item ? "비용 항목 수정" : "비용 항목 추가"}</DialogTitle>
        </DialogHeader>
        <div className="space-y-4 pt-4">
          <div className="space-y-2">
            <Label>항목명</Label>
            <Input value={name} onChange={(e) => setName(e.target.value)} />
          </div>
          <div className="space-y-2">
            <Label>비용 (원)</Label>
            <Input
              inputMode="numeric"
              value={amount}
              onChange={(e) => {
                const v = e.target.value.replace(/[^0-9]/g, "");
                setAmount(v);
              }}
              placeholder="숫자 입력"
            />
          </div>
          <div className="space-y-2">
            <Label>설명</Label>
            <Input
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="선택 사항"
            />
          </div>
          <div className="flex justify-end gap-2">
            <Button variant="outline" onClick={() => onOpenChange(false)}>
              취소
            </Button>
            <Button
              onClick={() =>
                onSubmit({
                  name,
                  amount: parseInt(amount) || 0,
                  description: description || null,
                })
              }
              disabled={!name || amount === "" || isPending}
            >
              {isPending && <Loader2 className="mr-1 h-3 w-3 animate-spin" />}
              {item ? "수정" : "추가"}
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}

export function CostSettingsTab() {
  const { data: items, isLoading } = useCostItems();
  const createItem = useCreateCostItem();
  const updateItem = useUpdateCostItem();
  const deleteItem = useDeleteCostItem();
  const saveDefaults = useSaveCostItemsDefaults();
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editing, setEditing] = useState<CostItemResponse | null>(null);

  async function handleSubmit(data: CostItemCreate) {
    try {
      if (editing) {
        await updateItem.mutateAsync({ itemId: editing.id, data });
        toast.success("비용 항목이 수정되었습니다");
      } else {
        await createItem.mutateAsync(data);
        toast.success("비용 항목이 추가되었습니다");
      }
      setDialogOpen(false);
      setEditing(null);
    } catch {
      toast.error("저장에 실패했습니다");
    }
  }

  async function handleDelete(id: string) {
    try {
      await deleteItem.mutateAsync(id);
      toast.success("비용 항목이 삭제되었습니다");
    } catch {
      toast.error("삭제에 실패했습니다");
    }
  }

  async function handleSaveDefaults() {
    if (!items) return;
    try {
      const defaultItems = items.map((item) => ({
        name: item.name,
        amount: item.amount,
        description: item.description,
      }));
      await saveDefaults.mutateAsync({ items: defaultItems });
      toast.success("기본값으로 저장되었습니다");
    } catch {
      toast.error("기본값 저장에 실패했습니다");
    }
  }

  if (isLoading) {
    return <div className="py-8 text-center text-muted-foreground">로딩 중...</div>;
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-end gap-2">
        <Button
          variant="outline"
          onClick={handleSaveDefaults}
          disabled={saveDefaults.isPending}
        >
          {saveDefaults.isPending && (
            <Loader2 className="mr-1 h-3 w-3 animate-spin" />
          )}
          기본값으로 저장
        </Button>
        <Button
          onClick={() => {
            setEditing(null);
            setDialogOpen(true);
          }}
        >
          <Plus className="mr-1 h-4 w-4" />
          비용 항목 추가
        </Button>
      </div>

      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>항목명</TableHead>
              <TableHead>비용</TableHead>
              <TableHead>설명</TableHead>
              <TableHead className="w-[100px]" />
            </TableRow>
          </TableHeader>
          <TableBody>
            {items?.map((item) => (
              <TableRow key={item.id}>
                <TableCell className="font-medium">{item.name}</TableCell>
                <TableCell>{formatCurrency(item.amount)}</TableCell>
                <TableCell className="text-muted-foreground">
                  {item.description ?? "-"}
                </TableCell>
                <TableCell>
                  <div className="flex gap-1">
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-7 w-7"
                      onClick={() => {
                        setEditing(item);
                        setDialogOpen(true);
                      }}
                    >
                      <Pencil className="h-3 w-3" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-7 w-7 text-destructive"
                      onClick={() => handleDelete(item.id)}
                    >
                      <Trash2 className="h-3 w-3" />
                    </Button>
                  </div>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      <CostItemFormDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        item={editing}
        onSubmit={handleSubmit}
        isPending={createItem.isPending || updateItem.isPending}
      />
    </div>
  );
}
