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

interface ListingCardProps {
  listing: Listing;
}

export function ListingCardWidget({ listing }: ListingCardProps) {
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

  // Определяем валюту для tooltip
  const tooltipCurrency = currency === 'USD' ? 'USD' : 'BYN';
  
  // Защита от undefined price
  const displayPrice = price ?? 0;

  return (
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
        <Badge className="absolute top-2 right-2 z-20" variant="secondary">
          {statusLabel}
        </Badge>
        {/* DealBadge отображается только если есть выгода */}
        {dealPercent !== null && dealPercent !== undefined && dealPercent < -10 && (
          <DealBadge dealPercent={dealPercent} />
        )}
        {/* PriceDropBadge отображается только если есть падение >= 5% */}
        {dropPercent !== null && dropPercent !== undefined && dropPercent >= 5 && (
          <PriceDropBadge dropPercent={dropPercent} />
        )}
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
}
