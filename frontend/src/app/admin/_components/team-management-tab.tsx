"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
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
import { Badge } from "@/components/ui/badge";
import {
  useTeamMembers,
  useCreateTeamMember,
  useUpdateTeamMember,
  useDeleteTeamMember,
  useSaveTeamMembersDefaults,
} from "@/hooks/use-settings";
import { toast } from "sonner";
import { Plus, Pencil, Trash2, Loader2 } from "lucide-react";
import { formatCurrencyManWon } from "@/lib/utils";
import type { TeamMemberCreate, TeamMemberResponse, TeamRole } from "@/lib/api/types";

const ROLES: TeamRole[] = ["PM", "FE", "BE", "MLE", "DevOps"];

function MemberFormDialog({
  open,
  onOpenChange,
  member,
  onSubmit,
  isPending,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  member: TeamMemberResponse | null;
  onSubmit: (data: TeamMemberCreate) => void;
  isPending: boolean;
}) {
  const [name, setName] = useState(member?.name ?? "");
  const [role, setRole] = useState<TeamRole>(member?.role ?? "BE");
  const [monthlyRate, setMonthlyRate] = useState(
    member?.monthly_rate?.toString() ?? "",
  );

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{member ? "팀원 수정" : "팀원 추가"}</DialogTitle>
        </DialogHeader>
        <div className="space-y-4 pt-4">
          <div className="space-y-2">
            <Label>이름</Label>
            <Input value={name} onChange={(e) => setName(e.target.value)} />
          </div>
          <div className="space-y-2">
            <Label>역할</Label>
            <Select value={role} onValueChange={(v) => setRole((v ?? "BE") as TeamRole)}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {ROLES.map((r) => (
                  <SelectItem key={r} value={r}>
                    {r}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <Label>월 단가 (원)</Label>
            <Input
              type="number"
              value={monthlyRate}
              onChange={(e) => setMonthlyRate(e.target.value)}
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
                  role,
                  monthly_rate: parseInt(monthlyRate) || 0,
                })
              }
              disabled={!name || !monthlyRate || isPending}
            >
              {isPending && <Loader2 className="mr-1 h-3 w-3 animate-spin" />}
              {member ? "수정" : "추가"}
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}

export function TeamManagementTab() {
  const { data: members, isLoading } = useTeamMembers();
  const createMember = useCreateTeamMember();
  const updateMember = useUpdateTeamMember();
  const deleteMember = useDeleteTeamMember();
  const saveDefaults = useSaveTeamMembersDefaults();
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editing, setEditing] = useState<TeamMemberResponse | null>(null);

  async function handleSubmit(data: TeamMemberCreate) {
    try {
      if (editing) {
        await updateMember.mutateAsync({ memberId: editing.id, data });
        toast.success("팀원이 수정되었습니다");
      } else {
        await createMember.mutateAsync(data);
        toast.success("팀원이 추가되었습니다");
      }
      setDialogOpen(false);
      setEditing(null);
    } catch {
      toast.error("저장에 실패했습니다");
    }
  }

  async function handleSaveDefaults() {
    if (!members) return;
    try {
      const items = members.map((m) => ({
        name: m.name,
        role: m.role as TeamMemberCreate["role"],
        monthly_rate: m.monthly_rate,
      }));
      await saveDefaults.mutateAsync({ items });
      toast.success("기본값으로 저장되었습니다");
    } catch {
      toast.error("기본값 저장에 실패했습니다");
    }
  }

  async function handleDelete(id: string) {
    try {
      await deleteMember.mutateAsync(id);
      toast.success("팀원이 삭제되었습니다");
    } catch {
      toast.error("삭제에 실패했습니다");
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
          팀원 추가
        </Button>
      </div>

      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>이름</TableHead>
              <TableHead>역할</TableHead>
              <TableHead>월 단가</TableHead>
              <TableHead>상태</TableHead>
              <TableHead className="w-[100px]" />
            </TableRow>
          </TableHeader>
          <TableBody>
            {members?.map((m) => (
              <TableRow key={m.id}>
                <TableCell className="font-medium">{m.name}</TableCell>
                <TableCell>
                  <Badge variant="secondary">{m.role}</Badge>
                </TableCell>
                <TableCell>{formatCurrencyManWon(m.monthly_rate)}</TableCell>
                <TableCell>
                  {m.is_available ? (
                    <Badge className="bg-green-100 text-green-700 hover:bg-green-100">
                      가용
                    </Badge>
                  ) : (
                    <Badge variant="outline">{m.current_project ?? "비가용"}</Badge>
                  )}
                </TableCell>
                <TableCell>
                  <div className="flex gap-1">
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-7 w-7"
                      onClick={() => {
                        setEditing(m);
                        setDialogOpen(true);
                      }}
                    >
                      <Pencil className="h-3 w-3" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-7 w-7 text-destructive"
                      onClick={() => handleDelete(m.id)}
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

      <MemberFormDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        member={editing}
        onSubmit={handleSubmit}
        isPending={createMember.isPending || updateMember.isPending}
      />
    </div>
  );
}
