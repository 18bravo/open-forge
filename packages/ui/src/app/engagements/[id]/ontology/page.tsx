'use client';

import * as React from 'react';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { cn } from '@/lib/utils';
import {
  ArrowRight,
  ChevronDown,
  ChevronRight,
  Code,
  Database,
  Edit,
  FileJson,
  Link as LinkIcon,
  Plus,
  Search,
  Table,
} from 'lucide-react';

// Mock ontology data
interface OntologyEntity {
  id: string;
  name: string;
  description?: string;
  type: 'object' | 'relationship' | 'property';
  properties?: OntologyProperty[];
  source?: string;
  relatedEntities?: { id: string; name: string; relationship: string }[];
}

interface OntologyProperty {
  name: string;
  type: string;
  nullable: boolean;
  description?: string;
  isPrimaryKey?: boolean;
  isForeignKey?: boolean;
  referencedEntity?: string;
}

const mockOntology: OntologyEntity[] = [
  {
    id: 'customer',
    name: 'Customer',
    description: 'Represents a customer in the system',
    type: 'object',
    source: 'Production PostgreSQL',
    properties: [
      { name: 'id', type: 'string', nullable: false, isPrimaryKey: true },
      { name: 'email', type: 'string', nullable: false },
      { name: 'name', type: 'string', nullable: true },
      { name: 'created_at', type: 'datetime', nullable: false },
      { name: 'segment_id', type: 'string', nullable: true, isForeignKey: true, referencedEntity: 'Segment' },
    ],
    relatedEntities: [
      { id: 'order', name: 'Order', relationship: 'has_many' },
      { id: 'segment', name: 'Segment', relationship: 'belongs_to' },
    ],
  },
  {
    id: 'order',
    name: 'Order',
    description: 'Represents a customer order',
    type: 'object',
    source: 'Production PostgreSQL',
    properties: [
      { name: 'id', type: 'string', nullable: false, isPrimaryKey: true },
      { name: 'customer_id', type: 'string', nullable: false, isForeignKey: true, referencedEntity: 'Customer' },
      { name: 'total_amount', type: 'decimal', nullable: false },
      { name: 'status', type: 'enum', nullable: false },
      { name: 'created_at', type: 'datetime', nullable: false },
    ],
    relatedEntities: [
      { id: 'customer', name: 'Customer', relationship: 'belongs_to' },
      { id: 'order_item', name: 'OrderItem', relationship: 'has_many' },
    ],
  },
  {
    id: 'product',
    name: 'Product',
    description: 'Represents a product in the catalog',
    type: 'object',
    source: 'Production PostgreSQL',
    properties: [
      { name: 'id', type: 'string', nullable: false, isPrimaryKey: true },
      { name: 'name', type: 'string', nullable: false },
      { name: 'price', type: 'decimal', nullable: false },
      { name: 'category', type: 'string', nullable: true },
      { name: 'sku', type: 'string', nullable: false },
    ],
    relatedEntities: [
      { id: 'order_item', name: 'OrderItem', relationship: 'has_many' },
    ],
  },
  {
    id: 'segment',
    name: 'Segment',
    description: 'Customer segment for analytics',
    type: 'object',
    source: 'S3 Data Lake',
    properties: [
      { name: 'id', type: 'string', nullable: false, isPrimaryKey: true },
      { name: 'name', type: 'string', nullable: false },
      { name: 'criteria', type: 'json', nullable: false },
    ],
    relatedEntities: [
      { id: 'customer', name: 'Customer', relationship: 'has_many' },
    ],
  },
];

interface OntologyPageProps {
  params: Promise<{ id: string }>;
}

export default function OntologyPage({ params }: OntologyPageProps) {
  const { id: engagementId } = React.use(params);
  const [search, setSearch] = React.useState('');
  const [selectedEntity, setSelectedEntity] = React.useState<OntologyEntity | null>(mockOntology[0]);
  const [expandedEntities, setExpandedEntities] = React.useState<Set<string>>(new Set(['customer']));

  const filteredEntities = mockOntology.filter((entity) =>
    entity.name.toLowerCase().includes(search.toLowerCase()) ||
    entity.description?.toLowerCase().includes(search.toLowerCase())
  );

  const toggleExpand = (id: string) => {
    setExpandedEntities((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-xl font-semibold">Ontology Schema</h2>
          <p className="text-sm text-muted-foreground">
            {mockOntology.length} entities discovered from connected data sources
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm">
            <FileJson className="mr-2 h-4 w-4" />
            Export JSON
          </Button>
          <Button size="sm">
            <Plus className="mr-2 h-4 w-4" />
            Add Entity
          </Button>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Entity List */}
        <Card className="lg:col-span-1">
          <CardHeader className="pb-3">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                placeholder="Search entities..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-9"
              />
            </div>
          </CardHeader>
          <CardContent className="p-0">
            <div className="divide-y max-h-[600px] overflow-y-auto">
              {filteredEntities.map((entity) => {
                const isExpanded = expandedEntities.has(entity.id);
                const isSelected = selectedEntity?.id === entity.id;

                return (
                  <div key={entity.id}>
                    <button
                      onClick={() => {
                        setSelectedEntity(entity);
                        toggleExpand(entity.id);
                      }}
                      className={cn(
                        'flex items-center gap-2 w-full px-4 py-3 text-left hover:bg-muted/50 transition-colors',
                        isSelected && 'bg-primary/5 border-l-2 border-primary'
                      )}
                    >
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          {isExpanded ? (
                            <ChevronDown className="h-4 w-4 text-muted-foreground flex-shrink-0" />
                          ) : (
                            <ChevronRight className="h-4 w-4 text-muted-foreground flex-shrink-0" />
                          )}
                          <Table className="h-4 w-4 text-primary flex-shrink-0" />
                          <span className="font-medium truncate">{entity.name}</span>
                        </div>
                        {entity.description && (
                          <p className="text-xs text-muted-foreground truncate pl-8 mt-0.5">
                            {entity.description}
                          </p>
                        )}
                      </div>
                      <span className="text-xs text-muted-foreground flex-shrink-0">
                        {entity.properties?.length || 0} props
                      </span>
                    </button>

                    {/* Expanded Properties Preview */}
                    {isExpanded && entity.properties && (
                      <div className="bg-muted/30 px-4 py-2 space-y-1">
                        {entity.properties.slice(0, 5).map((prop) => (
                          <div key={prop.name} className="flex items-center gap-2 text-xs pl-8">
                            <span className={cn(
                              'font-mono',
                              prop.isPrimaryKey && 'text-amber-600 dark:text-amber-400',
                              prop.isForeignKey && 'text-blue-600 dark:text-blue-400'
                            )}>
                              {prop.name}
                            </span>
                            <span className="text-muted-foreground">: {prop.type}</span>
                          </div>
                        ))}
                        {entity.properties.length > 5 && (
                          <p className="text-xs text-muted-foreground pl-8">
                            +{entity.properties.length - 5} more
                          </p>
                        )}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>

        {/* Entity Detail */}
        <Card className="lg:col-span-2">
          {selectedEntity ? (
            <>
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div>
                    <CardTitle className="flex items-center gap-2">
                      <Table className="h-5 w-5 text-primary" />
                      {selectedEntity.name}
                    </CardTitle>
                    {selectedEntity.description && (
                      <CardDescription className="mt-1">
                        {selectedEntity.description}
                      </CardDescription>
                    )}
                  </div>
                  <Button variant="outline" size="sm">
                    <Edit className="mr-2 h-4 w-4" />
                    Edit
                  </Button>
                </div>
                {selectedEntity.source && (
                  <div className="flex items-center gap-2 text-sm text-muted-foreground mt-2">
                    <Database className="h-4 w-4" />
                    Source: {selectedEntity.source}
                  </div>
                )}
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Properties */}
                <div>
                  <h4 className="text-sm font-medium mb-3">Properties</h4>
                  <div className="rounded-md border">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b bg-muted/50">
                          <th className="px-4 py-2 text-left font-medium">Name</th>
                          <th className="px-4 py-2 text-left font-medium">Type</th>
                          <th className="px-4 py-2 text-left font-medium">Nullable</th>
                          <th className="px-4 py-2 text-left font-medium">Reference</th>
                        </tr>
                      </thead>
                      <tbody>
                        {selectedEntity.properties?.map((prop) => (
                          <tr key={prop.name} className="border-b last:border-0">
                            <td className="px-4 py-2">
                              <div className="flex items-center gap-2">
                                <code className="font-mono">{prop.name}</code>
                                {prop.isPrimaryKey && (
                                  <span className="px-1.5 py-0.5 text-xs rounded bg-amber-100 text-amber-700 dark:bg-amber-900 dark:text-amber-300">
                                    PK
                                  </span>
                                )}
                                {prop.isForeignKey && (
                                  <span className="px-1.5 py-0.5 text-xs rounded bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300">
                                    FK
                                  </span>
                                )}
                              </div>
                            </td>
                            <td className="px-4 py-2">
                              <code className="text-xs bg-muted px-1.5 py-0.5 rounded">
                                {prop.type}
                              </code>
                            </td>
                            <td className="px-4 py-2">
                              {prop.nullable ? 'Yes' : 'No'}
                            </td>
                            <td className="px-4 py-2">
                              {prop.referencedEntity && (
                                <button
                                  onClick={() => {
                                    const ref = mockOntology.find(
                                      (e) => e.name === prop.referencedEntity
                                    );
                                    if (ref) setSelectedEntity(ref);
                                  }}
                                  className="flex items-center gap-1 text-primary hover:underline"
                                >
                                  <LinkIcon className="h-3 w-3" />
                                  {prop.referencedEntity}
                                </button>
                              )}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>

                {/* Relationships */}
                {selectedEntity.relatedEntities && selectedEntity.relatedEntities.length > 0 && (
                  <div>
                    <h4 className="text-sm font-medium mb-3">Relationships</h4>
                    <div className="grid gap-2 sm:grid-cols-2">
                      {selectedEntity.relatedEntities.map((rel) => (
                        <button
                          key={rel.id}
                          onClick={() => {
                            const entity = mockOntology.find((e) => e.id === rel.id);
                            if (entity) setSelectedEntity(entity);
                          }}
                          className="flex items-center justify-between p-3 rounded-lg border hover:bg-muted/50 transition-colors"
                        >
                          <div className="flex items-center gap-2">
                            <Table className="h-4 w-4 text-primary" />
                            <span className="font-medium">{rel.name}</span>
                          </div>
                          <div className="flex items-center gap-2">
                            <span className="text-xs text-muted-foreground">
                              {rel.relationship.replace('_', ' ')}
                            </span>
                            <ArrowRight className="h-4 w-4 text-muted-foreground" />
                          </div>
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </CardContent>
            </>
          ) : (
            <CardContent className="flex flex-col items-center justify-center py-12 text-center">
              <Code className="h-12 w-12 text-muted-foreground mb-4" />
              <h3 className="text-lg font-medium">Select an entity</h3>
              <p className="text-sm text-muted-foreground">
                Choose an entity from the list to view its schema
              </p>
            </CardContent>
          )}
        </Card>
      </div>
    </div>
  );
}
