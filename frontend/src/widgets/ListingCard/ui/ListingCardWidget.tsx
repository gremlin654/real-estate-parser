'use client';

import { Card, CardContent, CardFooter } from '@/shared/ui/card';
import { Badge } from '@/shared/ui/badge';
import { Button } from '@/shared/ui/button';
import { CITIES, STATUS_LABELS } from '@/shared/config';
import type { Listing } from '@/shared/types';
import { useNavigate } from 'react-router-dom';
import { useFilterStore } from '@/store/filterStore';
import { DealBadge } from '@/components/listing/DealBadge';
import { DealTooltip } from '@/components/listing/DealTooltip';
import { PriceDropBadge } from '@/components/listing/PriceDropBadge';
import { PriceDropTooltip } from '@/components/listing/PriceDropTooltip';
import { FavoriteButton } from '@/components/listing/FavoriteButton';
import { DealScoreBadge } from '@/components/listing/DealScoreBadge';
import { DealScoreTooltip } from '@/components/listing/DealScoreTooltip';
import { cn } from '@/shared/lib/utils';

interface ListingCardProps {
  listing: Listing;
  withFavoriteButton?: boolean;
}

export function ListingCardWidget({ listing, withFavoriteButton = true }: ListingCardProps) {
  const navigate = useNavigate();
  const { currency } = useFilterStore();
  const price = currency === 'USD' ? (listing.price_usd ?? listing.price) : listing.price;
  const city = listing.city ? CITIES[listing.city as keyof typeof CITIES] : null;
  const statusLabel = STATUS_LABELS[listing.status as keyof typeof STATUS_LABELS];
  const firstImage = listing.images?.[0];

  // Deal metrics
  const dealPercent = listing.deal_percent;
  const avgPricePerM2 = listing.avg_price_per_m2;
  const pricePerM2 = currency === 'USD' ? listing.price_per_m2_usd : listing.price_per_m2_byn;

  // Price Drop metrics
  const dropPercent = (listing as any).drop_percent;
  const maxPrice = (listing as any).max_price;
  const minPrice = (listing as any).min_price;

  // Deal Score metrics
  const dealScore = listing.deal_score;
  const dealLabel = listing.deal_label;
  const showDealScore = dealScore != null && dealScore >= 35;

  // Определяем валюту для tooltip
  const tooltipCurrency = currency === 'USD' ? 'USD' : 'BYN';

  // Защита от undefined price
  const displayPrice = price ?? 0;

  // Проверяем наличие DealBadge для позиционирования DealScoreBadge
  const hasDealBadge = dealPercent != null && dealPercent < -10;

  // Карточка с контентом
  const cardContent = (
    <Card className="group hover:shadow-lg transition-all duration-300 hover:-translate-y-1 overflow-hidden relative">
      <div className="relative aspect-video overflow-hidden">
        {firstImage ? (
          <img
            src={firstImage}
            alt={listing.title}
            className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-300"
          />
        ) : (
          <div className="w-full h-full bg-gradient-to-br from-muted to-muted/50 flex items-center justify-center">
            <span className="text-muted-foreground text-4xl">🏠</span>
          </div>
        )}
        {/* DealScoreBadge (слева вверху) */}
        {showDealScore && dealScore != null && dealLabel != null && (
          <div className={cn(
            'absolute z-30',
            hasDealBadge ? 'top-2 left-20' : 'top-2 left-2'
          )}>
            <DealScoreBadge
              score={dealScore}
              label={dealLabel}
              size="sm"
            />
          </div>
        )}
        {/* DealBadge отображается только если есть выгода (слева вверху) */}
        {hasDealBadge && (
          <DealBadge dealPercent={dealPercent} className="z-30" />
        )}
        {/* PriceDropBadge отображается только если есть падение >= 5% (справа внизу) */}
        {dropPercent !== null && dropPercent !== undefined && dropPercent >= 5 && (
          <PriceDropBadge dropPercent={dropPercent} className="z-20" />
        )}
        {/* FavoriteButton (справа вверху, левее Badge) */}
        {withFavoriteButton && (
          <FavoriteButton
            listingId={listing.id}
            size="sm"
            className="absolute top-2 right-2 z-30"
          />
        )}
        {/* Badge статуса (справа вверху, правее FavoriteButton) */}
        <Badge className="absolute top-2 right-10 z-20" variant="secondary">
          {statusLabel}
        </Badge>
      </div>

      <CardContent className="p-4 space-y-3">
        <div className="space-y-2">
          <h3 className="font-semibold text-lg line-clamp-2 group-hover:text-primary transition-colors">
            {listing.title}
          </h3>
          {/* Цена с DealTooltip если есть выгода */}
          {dealPercent !== null && dealPercent !== undefined && dealPercent < -10 && pricePerM2 && avgPricePerM2 ? (
            <DealTooltip
              currentPricePerM2={pricePerM2}
              avgPricePerM2={avgPricePerM2}
              dealPercent={dealPercent}
              currency={tooltipCurrency}
              area={listing.area}
            >
              <div className="text-2xl font-bold text-primary cursor-help hover:text-primary/80 transition-colors">
                {displayPrice.toLocaleString()} {currency}
              </div>
            </DealTooltip>
          ) : /* Цена с PriceDropTooltip если есть падение цены */
          dropPercent !== null && dropPercent !== undefined && dropPercent >= 5 && maxPrice && minPrice ? (
            <PriceDropTooltip
              maxPrice={maxPrice}
              minPrice={minPrice}
              currentPrice={displayPrice}
              dropPercent={dropPercent}
              currency={tooltipCurrency}
            >
              <div className="text-2xl font-bold text-primary cursor-help hover:text-primary/80 transition-colors">
                {displayPrice.toLocaleString()} {currency}
              </div>
            </PriceDropTooltip>
          ) : (
            <div className="text-2xl font-bold text-primary">
              {displayPrice.toLocaleString()} {currency}
            </div>
          )}
        </div>

        <div className="flex flex-wrap gap-2 text-sm text-muted-foreground">
          {listing.rooms && (
            <span className="flex items-center gap-1">
              <span>🛏️</span>
              {listing.rooms}-комн
            </span>
          )}
          {listing.area && (
            <span className="flex items-center gap-1">
              <span>📐</span>
              {listing.area} м²
            </span>
          )}
          {listing.floor && (
            <span className="flex items-center gap-1">
              <span>🏢</span>
              {listing.floor} эт.
            </span>
          )}
        </div>

        {city && (
          <Badge variant="outline" className="mt-2">
            {city}
          </Badge>
        )}
      </CardContent>

      <CardFooter className="p-4 pt-0">
        <Button
          className="w-full"
          onClick={() => navigate(`/listings/${listing.id}`)}
        >
          Подробнее
        </Button>
      </CardFooter>
    </Card>
  );

  // Wrap with DealScoreTooltip если есть breakdown
  if (showDealScore && listing.deal_score_breakdown) {
    return (
      <DealScoreTooltip
        dealScore={dealScore!}
        dealLabel={dealLabel || ''}
        breakdown={listing.deal_score_breakdown}
      >
        {cardContent}
      </DealScoreTooltip>
    );
  }

  return cardContent;
}
