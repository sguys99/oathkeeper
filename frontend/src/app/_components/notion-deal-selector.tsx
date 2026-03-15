"use client";

import { useState } from "react";
import { Check, ChevronsUpDown } from "lucide-react";
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from "@/components/ui/command";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { cn } from "@/lib/utils";
import type { NotionDeal } from "@/lib/api/types";

export function NotionDealSelector({
  deals,
  value,
  onSelect,
  disabled,
  importedPageIds,
}: {
  deals: NotionDeal[];
  value: NotionDeal | null;
  onSelect: (deal: NotionDeal | null) => void;
  disabled?: boolean;
  importedPageIds?: Set<string>;
}) {
  const [open, setOpen] = useState(false);

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger
        className="flex h-9 w-full items-center justify-between rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-xs disabled:cursor-not-allowed disabled:opacity-50"
        disabled={disabled}
      >
        <span className="truncate">
          {value ? value.deal_info : "Notion Deal을 선택하세요"}
        </span>
        <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
      </PopoverTrigger>
      <PopoverContent className="w-[--radix-popover-trigger-width] p-0" align="start">
        <Command>
          <CommandInput placeholder="Deal 검색..." />
          <CommandList>
            <CommandEmpty>Deal을 찾을 수 없습니다</CommandEmpty>
            <CommandGroup>
              {deals.map((deal) => {
                const isImported = importedPageIds?.has(deal.page_id) ?? false;
                return (
                  <CommandItem
                    key={deal.page_id}
                    value={deal.deal_info}
                    disabled={isImported}
                    onSelect={() => {
                      if (isImported) return;
                      onSelect(deal.page_id === value?.page_id ? null : deal);
                      setOpen(false);
                    }}
                  >
                    <Check
                      className={cn(
                        "mr-2 h-4 w-4",
                        value?.page_id === deal.page_id ? "opacity-100" : "opacity-0",
                      )}
                    />
                    <div className="flex flex-col">
                      <div className="flex items-center gap-2">
                        <span className={isImported ? "text-muted-foreground" : ""}>
                          {deal.deal_info}
                        </span>
                        {isImported && (
                          <span className="rounded bg-muted px-1.5 py-0.5 text-[10px] font-medium text-muted-foreground">
                            분석 완료
                          </span>
                        )}
                      </div>
                      {deal.customer_name && (
                        <span className="text-xs text-muted-foreground">
                          {deal.customer_name}
                          {deal.expected_amount
                            ? ` · ${(deal.expected_amount / 100_000_000).toFixed(1)}억원`
                            : ""}
                        </span>
                      )}
                    </div>
                  </CommandItem>
                );
              })}
            </CommandGroup>
          </CommandList>
        </Command>
      </PopoverContent>
    </Popover>
  );
}
